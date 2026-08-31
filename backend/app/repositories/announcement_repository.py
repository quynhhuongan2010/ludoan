from typing import Optional

from sqlalchemy import case
from sqlalchemy.orm import Session, joinedload

from app.models.announcement import Announcement
from app.schemas.announcement import AnnouncementCreate

# Ghim len dau, roi den do uu tien (khan > cao > binh_thuong > thap), roi moi nhat truoc.
_PRIORITY_RANK = case(
    {"khan": 0, "cao": 1, "binh_thuong": 2, "thap": 3},
    value=Announcement.priority,
    else_=2,
)
_ORDER = (Announcement.is_pinned.desc(), _PRIORITY_RANK.asc(), Announcement.created_at.desc())


def create(db: Session, ann_in: AnnouncementCreate, author_id: int) -> Announcement:
    ann = Announcement(**ann_in.model_dump(), author_id=author_id)
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return ann


def list_all(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    priority: Optional[str] = None,
    public_only: bool = False,
    pinned_only: bool = False,
) -> list[Announcement]:
    query = db.query(Announcement).options(joinedload(Announcement.author))
    if priority is not None:
        query = query.filter(Announcement.priority == priority)
    if public_only:
        query = query.filter(Announcement.is_public.is_(True))
    if pinned_only:
        query = query.filter(Announcement.is_pinned.is_(True))
    return query.order_by(*_ORDER).offset(skip).limit(limit).all()


def get_with_author(db: Session, ann_id: int) -> Announcement | None:
    return (
        db.query(Announcement)
        .options(joinedload(Announcement.author))
        .filter(Announcement.id == ann_id)
        .first()
    )


def get(db: Session, ann_id: int) -> Announcement | None:
    return db.get(Announcement, ann_id)


def update(db: Session, ann: Announcement, ann_in: AnnouncementCreate) -> Announcement:
    for field, value in ann_in.model_dump().items():
        setattr(ann, field, value)
    db.commit()
    db.refresh(ann)
    return ann


def delete(db: Session, ann: Announcement) -> None:
    db.delete(ann)
    db.commit()
