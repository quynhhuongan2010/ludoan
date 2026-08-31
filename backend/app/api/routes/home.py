from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.home import HomeSummaryOut, PublicHomeOut
from app.services import home_service

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/public", response_model=PublicHomeOut, status_code=status.HTTP_200_OK)
def get_public_home(
    limit: int = Query(default=6, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Trang cong khai cho khach chua dang nhap - khong can JWT."""
    return home_service.get_public_summary(db, limit)


@router.get(
    "/summary",
    response_model=HomeSummaryOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
def get_home_summary(
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return home_service.get_summary(db, current_user, limit)
