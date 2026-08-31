from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.models.user import User
from app.repositories import announcement_repository
from app.schemas.announcement import AnnouncementCreate, AnnouncementOut


def _to_out(ann: Announcement) -> AnnouncementOut:
    return AnnouncementOut(
        id=ann.id,
        title=ann.title,
        content=ann.content,
        priority=ann.priority,
        is_pinned=ann.is_pinned,
        is_public=ann.is_public,
        starts_at=ann.starts_at,
        ends_at=ann.ends_at,
        author_id=ann.author_id,
        author_full_name=ann.author.full_name,
        created_at=ann.created_at,
    )


def create_announcement(db: Session, ann_in: AnnouncementCreate, current_user: User) -> AnnouncementOut:
    ann = announcement_repository.create(db, ann_in, author_id=current_user.id)
    return _to_out(ann)


def list_announcements(
    db: Session,
    current_user: Optional[User],
    skip: int = 0,
    limit: int = 100,
    priority: Optional[str] = None,
    pinned_only: bool = False,
) -> list[AnnouncementOut]:
    anns = announcement_repository.list_all(
        db,
        skip=skip,
        limit=limit,
        priority=priority,
        public_only=current_user is None,
        pinned_only=pinned_only,
    )
    return [_to_out(a) for a in anns]


def get_announcement_or_404(db: Session, ann_id: int, current_user: Optional[User]) -> AnnouncementOut:
    ann = announcement_repository.get_with_author(db, ann_id)
    if ann is None or (current_user is None and not ann.is_public):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    return _to_out(ann)


def _get_owned_or_404(db: Session, ann_id: int, current_user: User) -> Announcement:
    ann = announcement_repository.get_with_author(db, ann_id)
    if ann is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    if current_user.role != "commander" and ann.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return ann


def update_announcement(
    db: Session, ann_id: int, ann_in: AnnouncementCreate, current_user: User
) -> AnnouncementOut:
    ann = _get_owned_or_404(db, ann_id, current_user)
    updated = announcement_repository.update(db, ann, ann_in)
    return _to_out(updated)


def delete_announcement(db: Session, ann_id: int, current_user: User) -> None:
    ann = _get_owned_or_404(db, ann_id, current_user)
    announcement_repository.delete(db, ann)
