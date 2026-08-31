from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.passwords import validate_password_strength, validate_username
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import unit_repository, user_repository
from app.schemas.user import (
    ChannelAccessUpdate,
    LoginRequest,
    PasswordChange,
    ProfileUpdate,
    RegisterRequest,
    Token,
    UserCreate,
)

VALID_ROLES = ("soldier", "officer", "commander", "admin")
SYSTEM_ACCOUNT_MSG = "Không thể khoá / hạ quyền / đổi tài khoản hệ thống"


def _check_role(role: str) -> None:
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Vai trò không hợp lệ. Cho phép: {', '.join(VALID_ROLES)}",
        )


def _check_unit_exists(db: Session, unit_id: int | None) -> None:
    if unit_id is not None and unit_repository.get(db, unit_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn vị không tồn tại")


def _guard_system_account(user: User) -> None:
    if user.is_system:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=SYSTEM_ACCOUNT_MSG)


def create_user(db: Session, user_in: UserCreate, current_user: User | None = None) -> User:
    validate_username(user_in.username)
    validate_password_strength(user_in.password)
    _check_role(user_in.role)
    if user_in.role == "admin" and (current_user is None or current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ tài khoản admin mới được tạo tài khoản admin khác",
        )
    if user_repository.get_by_username(db, user_in.username) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    _check_unit_exists(db, user_in.unit_id)

    return user_repository.create(
        db,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        unit_id=user_in.unit_id,
        directive_channel_access=user_in.directive_channel_access,
        command_channel_access=user_in.command_channel_access,
        # Tai khoan do nguoi khac cap -> buoc doi mat khau lan dau.
        # Tai khoan commander dau tien (bootstrap, chua co current_user) thi khong.
        must_change_password=current_user is not None,
    )


def register_user(db: Session, reg_in: RegisterRequest) -> User:
    """Tu dang ky o giao dien ngoai: luon role=soldier, is_active=False (cho commander kich hoat)."""
    validate_username(reg_in.username)
    validate_password_strength(reg_in.password)
    if user_repository.get_by_username(db, reg_in.username) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên đăng nhập đã tồn tại")

    user = User(
        username=reg_in.username,
        hashed_password=hash_password(reg_in.password),
        full_name=reg_in.full_name,
        role="soldier",
        is_active=False,
        clearance=False,
    )
    return user_repository.save(db, user)


def list_users(db: Session, skip: int = 0, limit: int = 100, is_active: bool | None = None) -> list[User]:
    return user_repository.list_all(db, skip, limit, is_active)


def has_any_user(db: Session) -> bool:
    return user_repository.count(db) > 0


def get_user_or_404(db: Session, user_id: int) -> User:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_user_visible_to(db: Session, user_id: int, current_user: User) -> User:
    if current_user.role not in ("commander", "admin") and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return get_user_or_404(db, user_id)


def _guard_last_commander(db: Session, user: User, *, changing_to_active: bool | None, changing_role: str | None) -> None:
    """Khong cho ha quyen / khoa tai khoan bac chi huy (commander/admin) cuoi cung dang hoat dong."""
    if user.role not in ("commander", "admin") or not user.is_active:
        return
    losing_commander = (changing_to_active is False) or (
        changing_role is not None and changing_role not in ("commander", "admin")
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
    _guard_last_commander(db, user, changing_to_active=is_active, changing_role=None)
    user.is_active = is_active
    return user_repository.save(db, user)


def set_user_clearance(db: Session, user_id: int, clearance: bool) -> User:
    user = get_user_or_404(db, user_id)
    user.clearance = clearance
    return user_repository.save(db, user)


def set_user_role(db: Session, user_id: int, role: str, current_user: User) -> User:
    _check_role(role)
    user = get_user_or_404(db, user_id)
    _guard_system_account(user)
    if role == "admin" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ tài khoản admin mới được cấp quyền admin",
        )
    if user.id == current_user.id and role not in ("commander", "admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự hạ quyền chỉ huy của chính mình",
        )
    _guard_last_commander(db, user, changing_to_active=None, changing_role=role)
    user.role = role
    return user_repository.save(db, user)


def set_user_unit(db: Session, user_id: int, unit_id: int | None) -> User:
    user = get_user_or_404(db, user_id)
    _check_unit_exists(db, unit_id)
    user.unit_id = unit_id
    return user_repository.save(db, user)


def set_user_channel_access(db: Session, user_id: int, payload: ChannelAccessUpdate) -> User:
    user = get_user_or_404(db, user_id)
    if payload.directive_channel_access is not None:
        user.directive_channel_access = payload.directive_channel_access
    if payload.command_channel_access is not None:
        user.command_channel_access = payload.command_channel_access
    return user_repository.save(db, user)


def reset_user_password(db: Session, user_id: int, new_password: str) -> None:
    user = get_user_or_404(db, user_id)
    if not user.is_system:
        validate_password_strength(new_password)
    user.hashed_password = hash_password(new_password)
    user.must_change_password = True
    user_repository.save(db, user)


def update_own_profile(db: Session, current_user: User, profile_in: ProfileUpdate) -> User:
    current_user.full_name = profile_in.full_name
    return user_repository.save(db, current_user)


def change_own_password(db: Session, current_user: User, password_in: PasswordChange) -> None:
    if not verify_password(password_in.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )
    if not current_user.is_system:
        validate_password_strength(password_in.new_password)
    current_user.hashed_password = hash_password(password_in.new_password)
    current_user.must_change_password = False
    user_repository.save(db, current_user)


def authenticate(db: Session, credentials: LoginRequest) -> Token:
    user = user_repository.get_by_username(db, credentials.username)
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa được kích hoạt — vui lòng chờ chỉ huy đơn vị duyệt",
        )

    access_token = create_access_token(
        subject=user.username,
        extra_claims={
            "role": user.role,
            "uid": user.id,
            "clr": bool(user.clearance),
            "unit": user.unit_id,
            "dca": bool(user.directive_channel_access),
            "cca": bool(user.command_channel_access),
            "mcp": bool(user.must_change_password),
            "adm": user.role == "admin",
        },
    )
    return Token(access_token=access_token)
