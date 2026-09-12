"""
Script kiem thu tu dong co che Rate Limiting & Chong Brute-force dang nhap (Step 3 - v7.3.0).
Kiem thu:
1. LoginBruteForceProtector: dem loi that bai, tu dong khoa sau 5 lan sai.
2. Chan 429 Too Many Requests khi dang trong thoi gian lockout, ke ca nhap dung mat khau.
3. Dang nhap thanh cong xoa sach bo dem loi.
4. Ghi nhan su kien vao audit_logs (LOGIN_LOCKOUT_TRIGGERED, LOGIN_BLOCKED_BRUTE_FORCE).
5. SlidingWindowRateLimiter: gioi han tan suat goi theo IP.
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.rate_limit import LoginBruteForceProtector, SlidingWindowRateLimiter, login_protector
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.user import LoginRequest
from app.services import user_service


def test_rate_limiting():
    print("=== BẮT ĐẦU KIỂM THỬ RATE LIMIT & CHỐNG BRUTE-FORCE (v7.3.0) ===")

    # 1. Test don le LoginBruteForceProtector
    protector = LoginBruteForceProtector(max_failures=5, failure_window_seconds=10, lockout_duration_seconds=20)
    test_ip = "192.168.1.199"
    test_user = "hacker_test"

    for i in range(1, 5):
        just_locked, rem = protector.record_failure(test_ip, test_user)
        assert not just_locked, f"Lần thứ {i} không được khóa"
        locked, _ = protector.is_locked_out(test_ip, test_user)
        assert not locked, f"Lần thứ {i} chưa bị khóa"
    print("-> [PASS] 4 lần đăng nhập sai đầu tiên chưa bị khóa.")

    # Lần thứ 5 sai -> Phải khóa!
    just_locked, rem = protector.record_failure(test_ip, test_user)
    assert just_locked, "Lần thứ 5 sai phải kích hoạt khóa ngay!"
    assert rem > 0
    locked, rem2 = protector.is_locked_out(test_ip, test_user)
    assert locked
    print(f"-> [PASS] Lần thứ 5 sai kích hoạt khóa thành công (thời gian khóa: {rem2}s).")

    # Đăng nhập thành công xóa khóa
    protector.record_success(test_ip, test_user)
    locked_after, _ = protector.is_locked_out(test_ip, test_user)
    assert not locked_after, "Đăng nhập thành công phải xóa sạch khóa!"
    print("-> [PASS] record_success giải phóng khóa và xóa bộ đếm lỗi.")

    # 2. Test SlidingWindowRateLimiter
    limiter = SlidingWindowRateLimiter(default_limit=3, window_seconds=5)
    ip_client = "10.0.0.15"

    allowed, rem, _ = limiter.check_request(ip_client)
    assert allowed and rem == 2
    allowed, rem, _ = limiter.check_request(ip_client)
    assert allowed and rem == 1
    allowed, rem, _ = limiter.check_request(ip_client)
    assert allowed and rem == 0
    # Lần thứ 4 vượt quá giới hạn 3 req/window
    allowed, rem, retry_after = limiter.check_request(ip_client)
    assert not allowed
    assert retry_after > 0
    print("-> [PASS] SlidingWindowRateLimiter chặn thành công khi vượt quá giới hạn tần suất.")

    # 3. Test tich hop voi user_service.authenticate va Audit Trail
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        # Reset login_protector singleton
        login_protector._failures.clear()
        login_protector._lockouts.clear()

        # Tạo user mẫu
        valid_user = User(
            username="thu_truong",
            hashed_password=hash_password("MatKhau@123"),
            full_name="Đại tá Thủ trưởng",
            role=1,
            clearance=True,
            is_active=True,
        )
        db.add(valid_user)
        db.commit()
        db.refresh(valid_user)

        client_ip = "192.168.10.88"
        target_username = "thu_truong"

        # Thử sai 4 lần
        for i in range(1, 5):
            try:
                user_service.authenticate(
                    db,
                    LoginRequest(username=target_username, password="wrong_password"),
                    ip_address=client_ip,
                )
                assert False, "Đăng nhập mật khẩu sai không được thành công"
            except HTTPException as e:
                assert e.status_code == 401
        print("-> [PASS] 4 lần sai trả về 401 Unauthorized.")

        # Lần 5 sai -> Phải trả về 429 Too Many Requests
        is_429 = False
        try:
            user_service.authenticate(
                db,
                LoginRequest(username=target_username, password="wrong_password"),
                ip_address=client_ip,
            )
        except HTTPException as e:
            if e.status_code == 429:
                is_429 = True
                assert "Retry-After" in e.headers
                print(f"-> [PASS] Lần 5 sai ném lỗi 429 Too Many Requests: {e.detail}")
        assert is_429, "Lần thứ 5 sai phải trả về HTTP 429!"

        # Khi đang bị khóa, dù nhập ĐÚNG mật khẩu cũng phải bị chặn 429
        is_still_blocked = False
        try:
            user_service.authenticate(
                db,
                LoginRequest(username=target_username, password="MatKhau@123"),
                ip_address=client_ip,
            )
        except HTTPException as e:
            if e.status_code == 429:
                is_still_blocked = True
                print("-> [PASS] Kẻ tấn công nhập đúng mật khẩu trong thời gian khóa vẫn bị chặn 429.")
        assert is_still_blocked, "Đang khóa phải từ chối xác thực!"

        # Kiểm tra Audit Trail có ghi nhận sự kiện khóa và chặn không
        logs = db.query(AuditLog).all()
        lockout_logs = [l for l in logs if l.action == "LOGIN_LOCKOUT_TRIGGERED"]
        blocked_logs = [l for l in logs if l.action == "LOGIN_BLOCKED_BRUTE_FORCE"]
        assert len(lockout_logs) >= 1, "Phải ghi nhận LOGIN_LOCKOUT_TRIGGERED trong audit_logs"
        assert len(blocked_logs) >= 1, "Phải ghi nhận LOGIN_BLOCKED_BRUTE_FORCE trong audit_logs"
        print("-> [PASS] Audit Trail ghi nhận đầy đủ sự kiện LOGIN_LOCKOUT_TRIGGERED và LOGIN_BLOCKED_BRUTE_FORCE.")

        # Mở khóa và đăng nhập lại bằng mật khẩu đúng -> Thành công
        login_protector.record_success(client_ip, target_username)
        token = user_service.authenticate(
            db,
            LoginRequest(username=target_username, password="MatKhau@123"),
            ip_address=client_ip,
        )
        assert token.access_token is not None
        print("-> [PASS] Sau khi giải phóng khóa, đăng nhập mật khẩu đúng thành công.")

        print("\n=== TẤT CẢ KIỂM THỬ RATE LIMIT & CHỐNG BRUTE-FORCE ĐÃ ĐẠT 100%! ===")

    finally:
        db.close()


if __name__ == "__main__":
    test_rate_limiting()
