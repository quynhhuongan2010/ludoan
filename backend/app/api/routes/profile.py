from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core import rbac
from app.models.user import User
from app.schemas.user import (
    PasswordChange,
    ProfileUpdate,
    UserOut,
    UserPermissionsOut,
)
from app.services import user_service

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/permissions", response_model=UserPermissionsOut, status_code=status.HTTP_200_OK)
def get_my_permissions(current_user: User = Depends(get_current_user)):
    """Tra ve ma tran phan quyen chi tiet va Khoi/Nganh co quan cua quan nhan."""
    matrix = rbac.get_permission_matrix(current_user)
    return UserPermissionsOut(
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        role=matrix["role"],
        role_label=current_user.role_label,
        branch=matrix["branch"],
        branch_label=matrix["branch_label"],
        unit_id=current_user.unit_id,
        unit_name=current_user.unit_name,
        permissions=matrix["permissions"],
    )


@router.put("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def update_my_profile(
    profile_in: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.update_own_profile(db, current_user, profile_in)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    password_in: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_service.change_own_password(db, current_user, password_in)
    return None
