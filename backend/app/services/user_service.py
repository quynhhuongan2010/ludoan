from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.passwords import validate_password_strength, validate_username
from app.core.roles import (
    COMMAND_ROLES,
    DEFAULT_REGISTER_ROLE,
    ROLE_ADMIN,
    USER_UNDELETABLE_ROLES,
    VALID_ROLES,
    coerce_role,
    is_admin,
    is_command,
    role_label,
)
from app.core.rate_limit import login_protector
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import unit_repository, user_repository
from app.services import audit_log_service
from app.schemas.user import (
    ChannelAccessUpdate,
    LoginRequest,
    PasswordChange,
    ProfileUpdate,
    RegisterRequest,
    Token,
    UserCreate,
    UserInfoUpdate,
)

SYSTEM_ACCOUNT_MSG = "Không thể khoá / hạ quyền / đổi tài khoản hệ thống"
_NEEDS_INFO_MSG = (
    "Cần bổ sung Cấp bậc, Chức danh (PATCH /users/{id}/info) và Đơn vị công tác "
    "(PATCH /users/{id}/unit) trước khi kích hoạt tài khoản này"
)


def _check_role(role) -> int:
    n = coerce_role(role)
    if n is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Vai trò không hợp lệ. Cho phép số nguyên: "
                + ", ".join(f"{r} ({role_label(r)})" for r in VALID_ROLES)
            ),
        )
    return n


def _check_unit_exists(db: Session, unit_id: int | None) -> None:
    if unit_id is not None and unit_repository.get(db, unit_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn vị không tồn tại")


def _guard_system_account(user: User) -> None:
    if user.is_system:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=SYSTEM_ACCOUNT_MSG)


def create_user(db: Session, user_in: UserCreate, current_user: User | None = None) -> User:
    validate_username(user_in.username)
    validate_password_strength(user_in.password)
    role = _check_role(user_in.role)
    if role == ROLE_ADMIN and (current_user is None or not is_admin(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ tài khoản admin mới được tạo tài khoản admin khác",
        )
    if user_repository.get_by_username(db, user_in.username) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên đăng nhập đã được sử dụng")
    _check_unit_exists(db, user_in.unit_id)

    return user_repository.create(
        db,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=role,
        rank=user_in.rank,
        position=user_in.position,
        unit_id=user_in.unit_id,
        directive_channel_access=user_in.directive_channel_access,
        command_channel_access=user_in.command_channel_access,
        # Tai khoan do nguoi khac cap -> buoc doi mat khau lan dau.
        # Tai khoan commander dau tien (bootstrap, chua co current_user) thi khong.
        must_change_password=current_user is not None,
    )


def register_user(db: Session, reg_in: RegisterRequest) -> User:
    """Tu dang ky o giao dien ngoai: luon role=5 (Nguoi dung), is_active=False (cho chi huy kich hoat).

    Chi can bo / QNCN co bien che thuc te moi duoc cap tai khoan mang noi bo - vi vay
    truoc khi kich hoat, chi huy phai bo sung Cap bac + Chuc danh (`PATCH .../info`)
    va Don vi (`PATCH .../unit`); thieu 1 trong 3 se khong kich hoat duoc
    (xem `set_user_active`).
    """
    validate_username(reg_in.username)
    validate_password_strength(reg_in.password)
    if user_repository.get_by_username(db, reg_in.username) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên đăng nhập đã tồn tại")

    user = User(
        username=reg_in.username,
        hashed_password=hash_password(reg_in.password),
        full_name=reg_in.full_name,
        role=DEFAULT_REGISTER_ROLE,
        is_active=False,
        clearance=False,
    )
    return user_repository.save(db, user)


def list_users(
    db: Session, skip: int = 0, limit: int = 100, is_active: bool | None = None
) -> dict:
    """Tra ve envelope phan trang: {items, total, skip, limit}."""
    return {
        "items": user_repository.list_all(db, skip, limit, is_active),
        "total": user_repository.count_filtered(db, is_active),
        "skip": skip,
        "limit": limit,
    }


def has_any_user(db: Session) -> bool:
    return user_repository.count(db) > 0


def get_user_or_404(db: Session, user_id: int) -> User:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài khoản")
    return user


def get_user_visible_to(db: Session, user_id: int, current_user: User) -> User:
    if not is_command(current_user) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không đủ quyền thực hiện thao tác này")
    return get_user_or_404(db, user_id)


def _guard_last_commander(db: Session, user: User, *, changing_to_active: bool | None, changing_role: int | None) -> None:
    """Khong cho ha quyen / khoa tai khoan bac chi huy (vai tro 0..3) cuoi cung dang hoat dong."""
    if not is_command(user) or not user.is_active:
        return
    losing_commander = (changing_to_active is False) or (
        changing_role is not None and changing_role not in COMMAND_ROLES
    )
    if losing_commander and user_repository.count_active_commanders(db, exclude_id=user.id) == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phải còn ít nhất một tài khoản chỉ huy đang hoạt động",
        )


def set_user_active(db: Session, user_id: int, is_active: bool, current_user: User) -> User:
    user = get_user_or_404(db, user_id)
    if user.id == current_user.id and not is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tự khoá tài khoản của chính mình")
    if not is_active:
        _guard_system_account(user)
    if is_active and (not user.rank or not user.position or user.unit_id is None):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_NEEDS_INFO_MSG)
    _guard_last_commander(db, user, changing_to_active=is_active, changing_role=None)
    user.is_active = is_active
    saved_user = user_repository.save(db, user)
    audit_log_service.record_action(
        db,
        action="user_activate" if is_active else "user_deactivate",
        actor=current_user,
        target_type="user",
        target_id=str(user.id),
        target_name=f"{user.full_name} ({user.username})",
        is_success=True,
        details="Kích hoạt tài khoản" if is_active else "Khoá tài khoản",
    )
    return saved_user


def _clean_user_foreign_keys(db: Session, user_id: int) -> None:
    """Xoá hoặc gỡ liên kết khoá ngoại trước khi xoá user để tránh IntegrityError."""
    from sqlalchemy import text
    tables_to_delete_by_user_id = [
        ("chat_participants", "user_id"),
        ("chat_messages", "sender_id"),
        ("official_dispatch_recipients", "user_id"),
        ("command_thread_participants", "user_id"),
        ("command_thread_messages", "sender_id"),
        ("command_thread_documents", "uploaded_by_id"),
        ("command_thread_reports", "generated_by_id"),
        ("directive_thread_recipients", "user_id"),
        ("directive_thread_messages", "sender_id"),
        ("directive_assignment_reports", "submitted_by_id"),
        ("directive_assignment_recipients", "assignee_id"),
        ("directive_acknowledgements", "user_id"),
        ("directive_reads", "user_id"),
    ]
    for tbl, col in tables_to_delete_by_user_id:
        try:
            db.execute(text(f"DELETE FROM {tbl} WHERE {col} = :uid"), {"uid": user_id})
        except Exception:
            pass

    try:
        db.execute(text("DELETE FROM leadership_tasks WHERE commander_id = :uid OR reported_by_id = :uid"), {"uid": user_id})
    except Exception:
        pass

    try:
        db.execute(text("DELETE FROM duty_shift_handovers WHERE giver_id = :uid OR receiver_id = :uid"), {"uid": user_id})
    except Exception:
        pass

    try:
        db.execute(text("DELETE FROM duty_week_plans WHERE author_id = :uid OR submitted_by_id = :uid OR reviewed_by_id = :uid"), {"uid": user_id})
    except Exception:
        pass

    try:
        db.execute(text("DELETE FROM duty_schedules WHERE author_id = :uid"), {"uid": user_id})
    except Exception:
        pass

    try:
        db.execute(text("DELETE FROM official_dispatches WHERE created_by_id = :uid"), {"uid": user_id})
    except Exception:
        pass

    for tbl, col in [
        ("command_threads", "created_by_id"),
        ("directive_threads", "created_by_id"),
        ("directive_assignments", "created_by_id"),
        ("directives", "author_id"),
        ("education_materials", "author_id"),
        ("posts", "author_id"),
        ("documents", "uploaded_by_id"),
        ("announcements", "author_id"),
        ("contacts", "created_by_id"),
        ("chat_conversations", "created_by_id"),
    ]:
        try:
            db.execute(text(f"DELETE FROM {tbl} WHERE {col} = :uid"), {"uid": user_id})
        except Exception:
            pass

    try:
        db.execute(text("UPDATE audit_logs SET actor_id = NULL WHERE actor_id = :uid"), {"uid": user_id})
    except Exception:
        pass


def delete_user(db: Session, user_id: int, current_user: User) -> None:
    """Xoa han mot tai khoan.
    
    Quy tac:
      - Khong the tu xoa chinh minh (400).
      - Neu la Admin (is_admin): Toan quyen xoa bat ky tai khoan nao ke ca tai khoan chi huy.
      - Neu la chi huy khac: Chan xoa tai khoan cap chi huy (0, 1, 2), chan xoa tai khoan he thong.
    """
    user = get_user_or_404(db, user_id)
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự xoá tài khoản của chính mình",
        )

    # Admin toan quyen xoa moi tai khoan
    if is_admin(current_user):
        if user.is_system and user.username == "admin":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Không thể xoá tài khoản quản trị hệ thống gốc (admin)",
            )
        _clean_user_foreign_keys(db, user.id)
    else:
        _guard_system_account(user)
        if coerce_role(user.role) in USER_UNDELETABLE_ROLES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Không thể xoá tài khoản cấp chỉ huy (Quản trị hệ thống / "
                    "Lữ trưởng - Chính uỷ / Lữ phó - Phó chính uỷ). Hãy hạ quyền "
                    "(PATCH /users/{id}/role) rồi xoá, hoặc khoá tài khoản."
                ),
            )
        _guard_last_commander(db, user, changing_to_active=False, changing_role=None)

    try:
        user_repository.delete(db, user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Tài khoản đã gắn với nội dung / hoạt động đã đăng nên không thể xoá. "
                "Hãy khoá tài khoản (deactivate) thay vì xoá."
            ),
        )


def set_user_info(db: Session, user_id: int, info_in: UserInfoUpdate) -> User:
    user = get_user_or_404(db, user_id)
    user.rank = info_in.rank
    user.position = info_in.position
    return user_repository.save(db, user)


def set_user_clearance(db: Session, user_id: int, clearance: bool, current_user: Optional[User] = None) -> User:
    user = get_user_or_404(db, user_id)
    user.clearance = clearance
    saved = user_repository.save(db, user)
    audit_log_service.record_action(
        db,
        action="user_clearance_change",
        actor=current_user,
        target_type="user",
        target_id=str(user.id),
        target_name=f"{user.full_name} ({user.username})",
        is_success=True,
        details="Cấp quyền xem MẬT" if clearance else "Thu hồi quyền xem MẬT",
    )
    return saved


def set_user_role(db: Session, user_id: int, role, current_user: User) -> User:
    role = _check_role(role)
    user = get_user_or_404(db, user_id)
    _guard_system_account(user)
    if role == ROLE_ADMIN and not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ tài khoản admin mới được cấp quyền admin",
        )
    if user.id == current_user.id and role not in COMMAND_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự hạ quyền chỉ huy của chính mình",
        )
    _guard_last_commander(db, user, changing_to_active=None, changing_role=role)
    old_role_name = role_label(user.role)
    user.role = role
    saved = user_repository.save(db, user)
    audit_log_service.record_action(
        db,
        action="user_role_change",
        actor=current_user,
        target_type="user",
        target_id=str(user.id),
        target_name=f"{user.full_name} ({user.username})",
        is_success=True,
        details=f"Đổi vai trò từ '{old_role_name}' sang '{role_label(role)}'",
    )
    return saved


def set_user_unit(db: Session, user_id: int, unit_id: int | None) -> User:
    user = get_user_or_404(db, user_id)
    _check_unit_exists(db, unit_id)
    user.unit_id = unit_id
    return user_repository.save(db, user)


def set_user_channel_access(
    db: Session,
    user_id: int,
    payload: ChannelAccessUpdate,
    current_user: Optional[User] = None,
) -> User:
    user = get_user_or_404(db, user_id)
    changes = []
    if payload.directive_channel_access is not None:
        user.directive_channel_access = payload.directive_channel_access
        changes.append(f"Kênh Chỉ đạo-Báo cáo: {'Bật' if payload.directive_channel_access else 'Tắt'}")
    if payload.command_channel_access is not None:
        user.command_channel_access = payload.command_channel_access
        changes.append(f"Kênh chuyên BCH: {'Bật' if payload.command_channel_access else 'Tắt'}")
    saved = user_repository.save(db, user)
    audit_log_service.record_action(
        db,
        action="user_channel_change",
        actor=current_user,
        target_type="user",
        target_id=str(user.id),
        target_name=f"{user.full_name} ({user.username})",
        is_success=True,
        details="; ".join(changes) if changes else "Cập nhật quyền kênh",
    )
    return saved


def reset_user_password(
    db: Session, user_id: int, new_password: str, current_user: Optional[User] = None
) -> None:
    user = get_user_or_404(db, user_id)
    if not user.is_system:
        validate_password_strength(new_password)
    user.hashed_password = hash_password(new_password)
    user.must_change_password = True
    user_repository.save(db, user)
    audit_log_service.record_action(
        db,
        action="user_reset_password",
        actor=current_user,
        target_type="user",
        target_id=str(user.id),
        target_name=f"{user.full_name} ({user.username})",
        is_success=True,
        details="Quản trị viên đặt lại mật khẩu và yêu cầu đổi ở lần đăng nhập tiếp theo",
    )


def update_own_profile(db: Session, current_user: User, profile_in: ProfileUpdate) -> User:
    current_user.full_name = profile_in.full_name
    return user_repository.save(db, current_user)


def change_own_password(db: Session, current_user: User, password_in: PasswordChange) -> None:
    if not verify_password(password_in.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Mật khẩu hiện tại không đúng"
        )
    if not current_user.is_system:
        validate_password_strength(password_in.new_password)
    current_user.hashed_password = hash_password(password_in.new_password)
    current_user.must_change_password = False
    user_repository.save(db, current_user)


def authenticate(
    db: Session, credentials: LoginRequest, ip_address: Optional[str] = None
) -> Token:
    # 1. Kiem tra lockout brute-force truoc khi xac thuc
    is_locked, remaining_seconds = login_protector.is_locked_out(ip_address, credentials.username)
    if is_locked:
        minutes = max(1, (remaining_seconds + 59) // 60)
        audit_log_service.record_action(
            db,
            action="LOGIN_BLOCKED_BRUTE_FORCE",
            actor=None,
            target_type="auth",
            target_name=credentials.username,
            ip_address=ip_address,
            is_success=False,
            details=f"Từ chối đăng nhập: tài khoản/IP đang bị tạm khóa (còn {minutes} phút)",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Tài khoản hoặc địa chỉ IP này đã nhập sai mật khẩu quá 5 lần. Vui lòng thử lại sau {minutes} phút để bảo vệ an toàn.",
            headers={"Retry-After": str(remaining_seconds)},
        )

    # 2. Xac thuc mat khau
    user = user_repository.get_by_username(db, credentials.username)
    if user is None or not verify_password(credentials.password, user.hashed_password):
        just_locked, rem_secs = login_protector.record_failure(ip_address, credentials.username)
        if just_locked:
            minutes = max(1, (rem_secs + 59) // 60)
            audit_log_service.record_action(
                db,
                action="LOGIN_LOCKOUT_TRIGGERED",
                actor=None,
                target_type="auth",
                target_name=credentials.username,
                ip_address=ip_address,
                is_success=False,
                details=f"Kích hoạt khóa tạm thời {minutes} phút do nhập sai mật khẩu 5 lần liên tiếp",
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Bạn đã nhập sai mật khẩu 5 lần liên tiếp. Tài khoản/IP đã bị tạm khóa {minutes} phút để bảo vệ an ninh.",
                headers={"Retry-After": str(rem_secs)},
            )

        audit_log_service.record_action(
            db,
            action="LOGIN_FAILED",
            actor=None,
            target_type="auth",
            target_name=credentials.username,
            ip_address=ip_address,
            is_success=False,
            details="Sai tên đăng nhập hoặc mật khẩu",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai tên đăng nhập hoặc mật khẩu")

    # 3. Dang nhap hop le -> Xoa bo dem that bai
    login_protector.record_success(ip_address, credentials.username)
    if not user.is_active:
        audit_log_service.record_action(
            db,
            action="auth_login",
            actor=user,
            target_type="auth",
            target_id=str(user.id),
            target_name=user.username,
            ip_address=ip_address,
            is_success=False,
            details="Tài khoản chưa được kích hoạt — đang chờ chỉ huy duyệt",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa được kích hoạt — vui lòng chờ chỉ huy đơn vị duyệt",
        )

    audit_log_service.record_action(
        db,
        action="auth_login",
        actor=user,
        target_type="auth",
        target_id=str(user.id),
        target_name=user.username,
        ip_address=ip_address,
        is_success=True,
        details="Đăng nhập thành công",
    )

    access_token = create_access_token(
        subject=user.username,
        extra_claims={
            "role": coerce_role(user.role),
            "uid": user.id,
            "clr": bool(user.clearance),
            "unit": user.unit_id,
            "dca": bool(user.directive_channel_access),
            "cca": bool(user.command_channel_access),
            "mcp": bool(user.must_change_password),
            "adm": is_admin(user),
        },
    )
    return Token(access_token=access_token, role=coerce_role(user.role))


def purge_test_users(db: Session, current_user: User) -> dict:
    """Xoá toàn bộ tài khoản thử nghiệm, chỉ giữ lại tài khoản admin đang đăng nhập."""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ tài khoản Quản trị hệ thống (Admin) mới có quyền dọn dẹp toàn bộ tài khoản thử nghiệm",
        )

    from sqlalchemy import text

    # Lấy tất cả user ngoại trừ user admin đang thao tác
    users_to_purge = db.query(User).filter(User.id != current_user.id).all()

    try:
        db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    except Exception:
        pass

    purged_count = 0
    for u in users_to_purge:
        # Giữ lại tài khoản is_system có username là admin nếu có
        if u.is_system and u.username == "admin":
            continue
        _clean_user_foreign_keys(db, u.id)
        db.delete(u)
        purged_count += 1

    try:
        db.commit()
    finally:
        try:
            db.execute(text("SET FOREIGN_KEY_CHECKS=1"))
            db.commit()
        except Exception:
            pass

    audit_log_service.record_action(
        db,
        action="user_purge_test_accounts",
        actor=current_user,
        target_type="system",
        target_id=None,
        target_name="Dọn dẹp tài khoản thử nghiệm",
        is_success=True,
        details=f"Đã xoá {purged_count} tài khoản thử nghiệm",
    )

    return {
        "purged_count": purged_count,
        "message": f"Đã dọn dẹp thành công {purged_count} tài khoản thử nghiệm.",
    }


def _resolve_unit_id(db: Session, raw_unit: Optional[str]) -> Optional[int]:
    """Ánh xạ tên đơn vị từ file vào unit_id trong CSDL."""
    from app.models.unit import Unit
    if not raw_unit or not str(raw_unit).strip():
        return None
    val = str(raw_unit).strip().lower()
    
    # 1. So khớp chính xác hoặc chứa trong tên
    units = db.query(Unit).all()
    for u in units:
        uname = u.name.lower().strip()
        if val == uname:
            return u.id

    # 2. So khớp từ khoá viết tắt quen thuộc trong quân đội
    mapping_keywords = [
        ("bch", "Ban chỉ huy Lữ đoàn"),
        ("ban chỉ huy", "Ban chỉ huy Lữ đoàn"),
        ("chỉ huy lữ đoàn", "Ban chỉ huy Lữ đoàn"),
        ("cấp uỷ", "Cấp uỷ – Đảng bộ Lữ đoàn"),
        ("đảng bộ", "Cấp uỷ – Đảng bộ Lữ đoàn"),
        ("tham mưu", "Phòng Tham mưu"),
        ("tm", "Phòng Tham mưu"),
        ("chính trị", "Phòng Chính trị"),
        ("ct", "Phòng Chính trị"),
        ("hậu cần", "Phòng Hậu cần – Kỹ thuật"),
        ("kỹ thuật", "Phòng Hậu cần – Kỹ thuật"),
        ("hckt", "Phòng Hậu cần – Kỹ thuật"),
        ("tiểu đoàn 1", "Tiểu đoàn 1"),
        ("d1", "Tiểu đoàn 1"),
        ("tiểu đoàn 2", "Tiểu đoàn 2"),
        ("d2", "Tiểu đoàn 2"),
        ("đại đội 5", "Đại đội 5"),
        ("c5", "Đại đội 5"),
        ("trung tâm 2", "Trung tâm 2"),
        ("tt2", "Trung tâm 2"),
        ("kiểm soát", "Trạm Kiểm soát"),
        ("bảo đảm", "Trạm bảo đảm"),
    ]
    for kw, target_name in mapping_keywords:
        if kw in val:
            for u in units:
                if u.name.lower() == target_name.lower():
                    return u.id

    # 3. Thử tìm chứa chuỗi
    for u in units:
        if u.name.lower() in val or val in u.name.lower():
            return u.id

    return None


def _resolve_role_from_text(raw_role: Optional[str | int]) -> int:
    """Ánh xạ chuỗi vai trò tiếng Việt sang mã số role 0..5."""
    if raw_role is None:
        return 4
    if isinstance(raw_role, int):
        return raw_role if raw_role in VALID_ROLES else 4
    s = str(raw_role).strip().lower()
    if s.isdigit():
        n = int(s)
        return n if n in VALID_ROLES else 4
    if "admin" in s or "quản trị" in s:
        return 0
    if "lữ trưởng" in s or "chính uỷ" in s or "lữ đoàn trưởng" in s or "bch" in s:
        return 1
    if "lữ phó" in s or "phó chính uỷ" in s or "phó lữ" in s:
        return 2
    if "chỉ huy" in s or "trưởng phòng" in s or "tiểu đoàn trưởng" in s or "đại đội trưởng" in s or "trạm trưởng" in s or "giám đốc" in s:
        return 3
    if "cá nhân" in s or "trợ lý" in s or "chiến sĩ" in s or "quân nhân" in s:
        return 4
    if "người dùng" in s:
        return 5
    return 4


def import_users_from_file(
    db: Session, file_bytes: bytes, filename: str, current_user: User
) -> dict:
    """Nhập người dùng hàng loạt từ file Excel (.xlsx, .xls) hoặc Word (.docx)."""
    import io
    from app.models.unit import Unit

    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ tài khoản Quản trị hệ thống (Admin) mới có quyền nhập người dùng từ file",
        )

    fn = filename.lower()
    raw_rows: list[dict] = []

    if fn.endswith((".xlsx", ".xls")):
        import openpyxl
        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            ws = wb.active
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể đọc file Excel: {str(e)}",
            )
        
        # Bóc tách các dòng
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File Excel rỗng hoặc không có dữ liệu quân nhân",
            )

        header = [str(cell or "").strip().lower() for cell in rows[0]]
        
        # Tìm vị trí các cột
        col_full_name = next((i for i, h in enumerate(header) if "họ" in h or "tên" in h and "đăng nhập" not in h), 1)
        col_username = next((i for i, h in enumerate(header) if "đăng nhập" in h or "username" in h or "tài khoản" in h), 2)
        col_password = next((i for i, h in enumerate(header) if "mật khẩu" in h or "pass" in h), 3)
        col_rank = next((i for i, h in enumerate(header) if "cấp bậc" in h or "quân hàm" in h), 4)
        col_position = next((i for i, h in enumerate(header) if "chức danh" in h or "chức vụ" in h), 5)
        col_unit = next((i for i, h in enumerate(header) if "đơn vị" in h or "phòng" in h or "tiểu đoàn" in h), 6)
        col_role = next((i for i, h in enumerate(header) if "vai trò" in h or "quyền" in h), 7)

        for row_idx, r in enumerate(rows[1:], start=2):
            if not r or all(c is None or str(c).strip() == "" for c in r):
                continue
            full_name = str(r[col_full_name]).strip() if col_full_name < len(r) and r[col_full_name] is not None else ""
            username = str(r[col_username]).strip() if col_username < len(r) and r[col_username] is not None else ""
            password = str(r[col_password]).strip() if col_password < len(r) and r[col_password] is not None else ""
            rank = str(r[col_rank]).strip() if col_rank < len(r) and r[col_rank] is not None else ""
            position = str(r[col_position]).strip() if col_position < len(r) and r[col_position] is not None else ""
            unit_str = str(r[col_unit]).strip() if col_unit < len(r) and r[col_unit] is not None else ""
            role_str = str(r[col_role]).strip() if col_role < len(r) and r[col_role] is not None else ""

            raw_rows.append({
                "row_index": row_idx,
                "full_name": full_name,
                "username": username,
                "password": password,
                "rank": rank,
                "position": position,
                "unit": unit_str,
                "role": role_str,
            })

    elif fn.endswith(".docx"):
        import docx
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể đọc file Word: {str(e)}",
            )
        
        if not doc.tables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File Word không chứa bảng dữ liệu quân nhân nào",
            )

        table = doc.tables[0]
        if len(table.rows) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bảng trong file Word không có dữ liệu quân nhân",
            )

        header = [cell.text.strip().lower() for cell in table.rows[0].cells]
        col_full_name = next((i for i, h in enumerate(header) if "họ" in h or "tên" in h and "đăng nhập" not in h), 1)
        col_username = next((i for i, h in enumerate(header) if "đăng nhập" in h or "username" in h or "tài khoản" in h), 2)
        col_password = next((i for i, h in enumerate(header) if "mật khẩu" in h or "pass" in h), 3)
        col_rank = next((i for i, h in enumerate(header) if "cấp bậc" in h or "quân hàm" in h), 4)
        col_position = next((i for i, h in enumerate(header) if "chức danh" in h or "chức vụ" in h), 5)
        col_unit = next((i for i, h in enumerate(header) if "đơn vị" in h or "phòng" in h or "tiểu đoàn" in h), 6)
        col_role = next((i for i, h in enumerate(header) if "vai trò" in h or "quyền" in h), 7)

        for row_idx, r in enumerate(table.rows[1:], start=2):
            cells = r.cells
            full_name = cells[col_full_name].text.strip() if col_full_name < len(cells) else ""
            username = cells[col_username].text.strip() if col_username < len(cells) else ""
            password = cells[col_password].text.strip() if col_password < len(cells) else ""
            rank = cells[col_rank].text.strip() if col_rank < len(cells) else ""
            position = cells[col_position].text.strip() if col_position < len(cells) else ""
            unit_str = cells[col_unit].text.strip() if col_unit < len(cells) else ""
            role_str = cells[col_role].text.strip() if col_role < len(cells) else ""

            if not username and not full_name:
                continue

            raw_rows.append({
                "row_index": row_idx,
                "full_name": full_name,
                "username": username,
                "password": password,
                "rank": rank,
                "position": position,
                "unit": unit_str,
                "role": role_str,
            })
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hệ thống chỉ hỗ trợ định dạng Excel (.xlsx, .xls) hoặc Word (.docx)",
        )

    # Đơn vị mặc định dự phòng nếu không nhận diện được
    default_unit = db.query(Unit).first()
    default_unit_id = default_unit.id if default_unit else None

    success_count = 0
    errors: list[dict] = []
    created_usernames: list[str] = []

    for item in raw_rows:
        row_idx = item["row_index"]
        username = item["username"]
        full_name = item["full_name"]
        raw_pwd = item["password"]
        rank = item["rank"] or "Đồng chí"
        position = item["position"] or "Quân nhân"
        unit_str = item["unit"]
        raw_role = item["role"]

        if not username:
            errors.append({"row_index": row_idx, "username": None, "error": "Thiếu tên đăng nhập"})
            continue

        # Chuẩn hoá username
        username = username.lower().replace(" ", "_")

        # Kiểm tra trùng lặp
        if user_repository.get_by_username(db, username) is not None:
            errors.append({"row_index": row_idx, "username": username, "error": f"Tên đăng nhập '{username}' đã tồn tại"})
            continue

        # Mật khẩu mặc định nếu trống
        password = raw_pwd if raw_pwd and len(raw_pwd) >= 6 else "LuDoan21@2026"

        # Ánh xạ đơn vị và vai trò
        unit_id = _resolve_unit_id(db, unit_str) or default_unit_id
        role = _resolve_role_from_text(raw_role)

        try:
            new_user = User(
                username=username,
                hashed_password=hash_password(password),
                full_name=full_name or username,
                role=role,
                rank=rank,
                position=position,
                unit_id=unit_id,
                is_active=True,
                clearance=role <= 3,
                directive_channel_access=role <= 3,
                command_channel_access=role <= 2,
                must_change_password=False,
            )
            db.add(new_user)
            db.flush()
            success_count += 1
            created_usernames.append(username)
        except Exception as ex:
            errors.append({"row_index": row_idx, "username": username, "error": str(ex)})

    db.commit()

    audit_log_service.record_action(
        db,
        action="user_import_batch",
        actor=current_user,
        target_type="system",
        target_id=None,
        target_name=filename,
        is_success=True,
        details=f"Đã nhập thành công {success_count}/{len(raw_rows)} tài khoản từ file {filename}",
    )

    return {
        "total_rows": len(raw_rows),
        "success_count": success_count,
        "error_count": len(errors),
        "errors": errors,
        "created_usernames": created_usernames,
    }


def generate_user_template(template_format: str) -> tuple[bytes, str, str]:
    """Sinh file mẫu Excel (.xlsx) hoặc Word (.docx) chuẩn quân sự để nhập người dùng."""
    import io
    fmt = template_format.lower().strip()

    sample_data = [
        (1, "Nguyễn Văn Thắng", "lu_truong", "LuDoan21@2026", "Đại tá", "Lữ đoàn trưởng", "Ban chỉ huy Lữ đoàn", "Lữ trưởng - Chính uỷ"),
        (2, "Trần Văn Nam", "chinh_uy", "LuDoan21@2026", "Đại tá", "Chính uỷ", "Ban chỉ huy Lữ đoàn", "Lữ trưởng - Chính uỷ"),
        (3, "Lê Văn Hải", "lu_pho_tm", "LuDoan21@2026", "Thượng tá", "Phó Lữ trưởng kiêm TMT", "Ban chỉ huy Lữ đoàn", "Lữ phó - Phó chính uỷ"),
        (4, "Đỗ Văn Cường", "tm_truong", "LuDoan21@2026", "Trung tá", "Trưởng phòng Tham mưu", "Phòng Tham mưu", "Chỉ huy đơn vị"),
        (5, "Hoàng Văn Dũng", "d1_truong", "LuDoan21@2026", "Thiếu tá", "Tiểu đoàn trưởng", "Tiểu đoàn 1", "Chỉ huy đơn vị"),
        (6, "Vũ Tuấn Anh", "tro_ly_tac_chien", "LuDoan21@2026", "Thiếu tá", "Trợ lý Tác chiến", "Phòng Tham mưu", "Cá nhân"),
        (7, "Đặng Thành Vinh", "tram_kiem_soat", "LuDoan21@2026", "Đại uý", "Trạm trưởng", "Trạm Kiểm soát", "Chỉ huy đơn vị"),
    ]

    headers = [
        "STT", "Họ và tên", "Tên đăng nhập", "Mật khẩu", "Cấp bậc", "Chức danh", "Đơn vị", "Vai trò"
    ]

    if fmt in ("excel", "xlsx"):
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "DS Quân nhân"

        # Định dạng màu xanh áo lính quân đội #1B4D3E
        header_fill = PatternFill(start_color="1B4D3E", end_color="1B4D3E", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin", color="CCCCCC"),
            right=Side(style="thin", color="CCCCCC"),
            top=Side(style="thin", color="CCCCCC"),
            bottom=Side(style="thin", color="CCCCCC"),
        )
        center_align = Alignment(horizontal="center", vertical="center")
        left_align = Alignment(horizontal="left", vertical="center")

        ws.append(headers)
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align

        for row in sample_data:
            ws.append(list(row))
            cur_row = ws.max_row
            for col_num in range(1, len(headers) + 1):
                c = ws.cell(row=cur_row, column=col_num)
                c.border = thin_border
                c.alignment = center_align if col_num in (1, 4, 8) else left_align

        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 5, 12)

        buf = io.BytesIO()
        wb.save(buf)
        return (
            buf.getvalue(),
            "mau_nhap_quan_nhan_ludoan21.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    else:
        # Word (.docx)
        import docx
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = docx.Document()
        title = doc.add_heading("LỮ ĐOÀN THÔNG TIN 21 - BẢNG MẪU NHẬP QUÂN NHÂN", level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p = doc.add_paragraph(
            "Hướng dẫn: Đồng chí nhập danh sách cán bộ, chiến sĩ vào bảng dưới đây theo mẫu. "
            "Sau khi điền đủ thông tin, lưu tệp .docx và tải lên hệ thống tại mục Quản lý người dùng."
        )
        p.paragraph_format.italic = True

        table = doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"

        hdr_cells = table.rows[0].cells
        for idx, text in enumerate(headers):
            hdr_cells[idx].text = text
            for paragraph in hdr_cells[idx].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(27, 77, 62)

        for row in sample_data:
            row_cells = table.add_row().cells
            for idx, val in enumerate(row):
                row_cells[idx].text = str(val)

        buf = io.BytesIO()
        doc.save(buf)
        return (
            buf.getvalue(),
            "mau_nhap_quan_nhan_ludoan21.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

