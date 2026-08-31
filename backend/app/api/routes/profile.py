from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import PasswordChange, ProfileUpdate, UserOut
from app.services import user_service

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


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
