from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.post import Post
from app.schemas.post import PostCreate

_ORDER = Post.created_at.desc()


def create(db: Session, post_in: PostCreate, author_id: int, status: str) -> Post:
    post = Post(**post_in.model_dump(), author_id=author_id, status=status)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def list_all(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    statuses: Optional[Sequence[str]] = None,
    classifications: Optional[Sequence[str]] = None,
    featured_only: bool = False,
) -> list[Post]:
    query = db.query(Post).options(joinedload(Post.author))
    if category is not None:
        query = query.filter(Post.category == category)
    if statuses is not None:
        query = query.filter(Post.status.in_(list(statuses)))
    if classifications is not None:
        query = query.filter(Post.classification.in_(list(classifications)))
    if featured_only:
        query = query.filter(Post.is_featured.is_(True))
    return query.order_by(_ORDER).offset(skip).limit(limit).all()


def list_for_author(
    db: Session,
    *,
    author_id: int,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    also_status: str = "da_duyet",
    classifications: Optional[Sequence[str]] = None,
) -> list[Post]:
    """Bai (o trang thai `also_status` VA thuoc `classifications`) HOAC bai do chinh tac gia nay dang."""
    query = db.query(Post).options(joinedload(Post.author))
    if category is not None:
        query = query.filter(Post.category == category)
    approved = Post.status == also_status
    if classifications is not None:
        approved = approved & Post.classification.in_(list(classifications))
    query = query.filter(or_(approved, Post.author_id == author_id))
    return query.order_by(_ORDER).offset(skip).limit(limit).all()


def get_with_author(db: Session, post_id: int) -> Post | None:
    return db.query(Post).options(joinedload(Post.author)).filter(Post.id == post_id).first()


def get(db: Session, post_id: int) -> Post | None:
    return db.get(Post, post_id)


def slug_taken(db: Session, slug: str, exclude_id: Optional[int] = None) -> bool:
    query = db.query(Post.id).filter(Post.slug == slug)
    if exclude_id is not None:
        query = query.filter(Post.id != exclude_id)
    return db.query(query.exists()).scalar()


def set_status(
    db: Session,
    post: Post,
    *,
    status: str,
    clear_review: bool = False,
) -> Post:
    post.status = status
    if clear_review:
        post.review_note = None
        post.reviewed_by_id = None
        post.reviewed_at = None
    db.commit()
    db.refresh(post)
    return post


def update(db: Session, post: Post, post_in: PostCreate) -> Post:
    for field, value in post_in.model_dump().items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post


def save(db: Session, post: Post) -> Post:
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def set_review(db: Session, post: Post, *, status: str, review_note: Optional[str], reviewer_id: int) -> Post:
    post.status = status
    post.review_note = review_note
    post.reviewed_by_id = reviewer_id
    post.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(post)
    return post


def delete(db: Session, post: Post) -> None:
    db.delete(post)
    db.commit()
