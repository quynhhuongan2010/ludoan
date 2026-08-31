from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories import user_repository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = user_repository.get_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

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


def require_roles(*allowed_roles: str):
    # `admin` la bac cao nhat: ke thua toan bo quyen cua `commander`.
    effective = set(allowed_roles)
    if "commander" in effective:
        effective.add("admin")

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in effective:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return current_user

    return dependency


def bootstrap_or_role(*allowed_roles: str):
    """Cho phep goi khong can dang nhap NEU chua co user nao trong he thong
    (khoi tao tai khoan commander dau tien); nguoc lai bat buoc dung role."""

    effective = set(allowed_roles)
    if "commander" in effective:
        effective.add("admin")

    def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        db: Session = Depends(get_db),
    ) -> None:
        if not user_repository.count(db):
            return

        current_user = get_current_user(credentials, db)
        if current_user.role not in effective:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return dependency
