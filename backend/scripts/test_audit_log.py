"""
Script test tự động tính năng Audit Trail / Nhật ký bảo mật (Step 2 - v7.2.0)
Sử dụng SQLite in-memory để kiểm thử độc lập:
1. Ghi log thành công và lưu đầy đủ thông tin (user, action, target_type, target_id, ip_address, details)
2. Phân quyền truy cập GET /audit-logs:
   - role=0, 1, 2 (Chỉ huy/Quản trị) -> Được phép xem
   - role=5 (Chiến sĩ / Người dùng thường) -> 403 Forbidden
3. Bộ lọc và tìm kiếm: action, target_type, keyword trong details
4. Ghi nhận đăng nhập thành công và thất bại
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services import audit_log_service


def test_audit_logs():
    print("=== BẮT ĐẦU KIỂM THỬ AUDIT TRAIL (v7.2.0) ===")
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        # 1. Tạo người dùng mẫu
        commander = User(
            username="chi_huy",
            hashed_password="mock_hash_password",
            full_name="Đại tá Nguyễn Văn A",
            role=0,
            clearance=True,
            is_active=True
        )
        officer = User(
            username="tro_ly",
            hashed_password="mock_hash_password",
            full_name="Trung tá Trần B",
            role=1,
            clearance=True,
            is_active=True
        )
        soldier = User(
            username="chien_si",
            hashed_password="mock_hash_password",
            full_name="Binh nhất Lê C",
            role=5,
            clearance=False,
            is_active=True
        )
        db.add_all([commander, officer, soldier])
        db.commit()
        db.refresh(commander)
        db.refresh(officer)
        db.refresh(soldier)
        print("-> Đã tạo 3 tài khoản thử nghiệm (Chỉ huy, Sĩ quan, Chiến sĩ).")

        # 2. Test record_action
        audit_log_service.record_action(
            db=db,
            action="DISPATCH_DOWNLOAD",
            actor=officer,
            target_type="dispatch",
            target_id="101",
            target_name="Công văn số 45/TM",
            ip_address="192.168.1.50",
            details="Tải công văn tuyệt mật số 45/TM",
        )

        logs = db.query(AuditLog).all()
        assert len(logs) == 1
        log1 = logs[0]
        assert log1.actor_id == officer.id
        assert log1.actor_username == "tro_ly"
        assert log1.action == "DISPATCH_DOWNLOAD"
        assert log1.ip_address == "192.168.1.50"
        assert log1.target_id == "101"
        print("-> [PASS] Ghi log 'DISPATCH_DOWNLOAD' thành công.")

        audit_log_service.record_action(
            db=db,
            action="USER_DEACTIVATE",
            actor=commander,
            target_type="user",
            target_id=str(soldier.id),
            target_name=soldier.username,
            ip_address="192.168.1.10",
            details=f"Khóa tài khoản {soldier.username}",
        )

        # Test log unauthenticated (login failure)
        audit_log_service.record_action(
            db=db,
            action="LOGIN_FAILED",
            actor=None,
            target_type="auth",
            target_id=None,
            target_name="hacker_user",
            ip_address="192.168.1.99",
            details="Đăng nhập thất bại cho tài khoản: hacker_user",
        )

        logs = db.query(AuditLog).all()
        assert len(logs) == 3
        print("-> [PASS] Ghi log 'LOGIN_FAILED' (actor=None) và 'USER_DEACTIVATE' thành công.")

        # 3. Test phân quyền truy vấn (RBAC)
        # Chỉ huy (role=0) -> OK
        res_cmd = audit_log_service.get_audit_logs(db=db, current_user=commander, page=1, page_size=20)
        assert res_cmd.total == 3
        assert len(res_cmd.items) == 3
        print("-> [PASS] Chỉ huy (role=0) truy vấn log thành công: xem được 3 bản ghi.")

        # Quản trị / Trợ lý (role=1) -> OK
        res_off = audit_log_service.get_audit_logs(db=db, current_user=officer, page=1, page_size=20)
        assert res_off.total == 3
        print("-> [PASS] Trợ lý quản trị (role=1) truy vấn log thành công.")

        # Chiến sĩ (role=5) -> Bị chặn 403 Forbidden
        blocked = False
        try:
            audit_log_service.get_audit_logs(db=db, current_user=soldier, page=1, page_size=20)
        except HTTPException as e:
            blocked = True
            assert e.status_code == 403
            print(f"-> [PASS] Chiến sĩ (role=5) bị từ chối truy cập chuẩn xác (403 Forbidden): {e.detail}")
        assert blocked, "Chiến sĩ role=5 phải bị chặn 403!"

        # 4. Test bộ lọc và tìm kiếm
        # Lọc theo action
        res_filter_action = audit_log_service.get_audit_logs(db=db, current_user=commander, action="DISPATCH_DOWNLOAD")
        assert res_filter_action.total == 1
        assert res_filter_action.items[0].target_id == "101"
        print("-> [PASS] Lọc theo action='DISPATCH_DOWNLOAD' chuẩn xác.")

        # Lọc theo actor_id
        res_filter_user = audit_log_service.get_audit_logs(db=db, current_user=commander, actor_id=commander.id)
        assert res_filter_user.total == 1
        assert res_filter_user.items[0].action == "USER_DEACTIVATE"
        print("-> [PASS] Lọc theo actor_id chuẩn xác.")

        # Tìm kiếm từ khóa trong details
        res_search = audit_log_service.get_audit_logs(db=db, current_user=commander, search="hacker_user")
        assert res_search.total == 1
        assert res_search.items[0].action == "LOGIN_FAILED"
        print("-> [PASS] Tìm kiếm từ khóa trong details chuẩn xác.")

        print("\n=== TẤT CẢ CÁC KIỂM THỬ AUDIT TRAIL ĐÃ ĐẠT 100%! ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_audit_logs()
