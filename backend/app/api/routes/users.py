from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import (
    bootstrap_or_role,
    get_current_user,
    get_optional_user,
    require_roles,
)
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import (
    ChannelAccessUpdate,
    ClearanceUpdate,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    RoleUpdate,
    Token,
    UnitAssignUpdate,
    UserCreate,
    UserOut,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(bootstrap_or_role("commander"))],
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return user_service.create_user(db, user_in, current_user)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(reg_in: RegisterRequest, db: Session = Depends(get_db)):
    """Tu dang ky tai khoan tu giao dien ngoai. Tao role=soldier, chua kich hoat."""
    return user_service.register_user(db, reg_in)


@router.get(
    "/",
    response_model=list[UserOut],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("commander"))],
)
def list_users(
    skip: int = 0,
    limit: int = 100,
    active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return user_service.list_users(db, skip, limit, active)


@router.get("/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return user_service.get_user_visible_to(db, user_id, current_user)


@router.post(
    "/{user_id}/activate",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("commander"))],
)
def activate_user(
    user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return user_service.set_user_active(db, user_id, True, current_user)


@router.post(
    "/{user_id}/deactivate",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("commander"))],
)
def deactivate_user(
    user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return user_service.set_user_active(db, user_id, False, current_user)


@router.patch(
    "/{user_id}/clearance",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("commander"))],
)
def set_clearance(user_id: int, payload: ClearanceUpdate, db: Session = Depends(get_db)):
    return user_service.set_user_clearance(db, user_id, payload.clearance)


@router.patch(
    "/{user_id}/role",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("commander"))],
)
def set_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.set_user_role(db, user_id, payload.role, current_user)


@router.patch(
    "/{user_id}/unit",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("commander"))],
)
def set_unit(user_id: int, payload: UnitAssignUpdate, db: Session = Depends(get_db)):
    return user_service.set_user_unit(db, user_id, payload.unit_id)


@router.patch(
    "/{user_id}/channel-access",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("admin"))],
)
def set_channel_access(user_id: int, payload: ChannelAccessUpdate, db: Session = Depends(get_db)):
    return user_service.set_user_channel_access(db, user_id, payload)


@router.post(
    "/{user_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
def reset_password(user_id: int, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user_service.reset_user_password(db, user_id, payload.new_password)
    return None


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    return user_service.authenticate(db, credentials)
