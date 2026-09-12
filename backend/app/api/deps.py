from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.roles import coerce_role
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories import user_repository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chưa đăng nhập")

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thông tin phiên đăng nhập không hợp lệ",
        )

    user = user_repository.get_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Không tìm thấy tài khoản")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản chưa được kích hoạt")

    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Tra ve User neu co JWT hop le, nguoc lai None (khong raise 401).
    Dung cho endpoint cong khai co hanh vi khac nhau giua khach va nguoi da dang nhap."""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        return None
    username = payload.get("sub")
    if username is None:
        return None
    user = user_repository.get_by_username(db, username)
    if user is None or not user.is_active:
        return None
    return user


def resolve_ws_user(db: Session, token: str) -> User | None:
    """Xac thuc token JWT truyen qua query-string cua ket noi WebSocket.

    Tra ve User neu token hop le va tai khoan dang hoat dong; nguoc lai None
    (KHONG raise - handler WebSocket tu dong dong ket noi khi nhan None)."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except JWTError:
        return None
    username = payload.get("sub")
    if not username:
        return None
    user = user_repository.get_by_username(db, username)
    if user is None or not user.is_active:
        return None
    return user


def require_roles(*allowed_roles: int):
    """Chan 403 neu vai tro (so nguyen 0..5) cua tai khoan khong nam trong danh sach.

    Truyen thang cac hang so tu `app.core.roles` (COMMAND_ROLES / CONTENT_ROLES /
    ADMIN_ROLES) hoac tung gia tri cu the.
    """
    effective = {coerce_role(r) for r in allowed_roles}

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if coerce_role(current_user.role) not in effective:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không đủ quyền thực hiện thao tác này")
        return current_user

    return dependency


def bootstrap_or_role(*allowed_roles: int):
    """Cho phep goi khong can dang nhap NEU chua co user nao trong he thong
    (khoi tao tai khoan chi huy dau tien); nguoc lai bat buoc dung vai tro."""

    effective = {coerce_role(r) for r in allowed_roles}

    def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        db: Session = Depends(get_db),
    ) -> None:
        if not user_repository.count(db):
            return

        current_user = get_current_user(credentials, db)
        if coerce_role(current_user.role) not in effective:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không đủ quyền thực hiện thao tác này")

    return dependency
