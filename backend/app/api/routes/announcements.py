from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user, require_roles
from app.core.database import get_db
from app.core.roles import CONTENT_ROLES
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementOut
from app.services import announcement_service

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.post(
    "",
    response_model=AnnouncementOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def create_announcement(
    ann_in: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return announcement_service.create_announcement(db, ann_in, current_user)


@router.get("", response_model=list[AnnouncementOut], status_code=status.HTTP_200_OK)
def list_announcements(
    skip: int = 0,
    limit: int = 100,
    priority: Optional[str] = None,
    pinned_only: bool = False,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return announcement_service.list_announcements(db, current_user, skip, limit, priority, pinned_only)


@router.get("/{ann_id}", response_model=AnnouncementOut, status_code=status.HTTP_200_OK)
def get_announcement(
    ann_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return announcement_service.get_announcement_or_404(db, ann_id, current_user)


@router.put(
    "/{ann_id}",
    response_model=AnnouncementOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def update_announcement(
    ann_id: int,
    ann_in: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return announcement_service.update_announcement(db, ann_id, ann_in, current_user)


@router.delete(
    "/{ann_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def delete_announcement(
    ann_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    announcement_service.delete_announcement(db, ann_id, current_user)
    return None
