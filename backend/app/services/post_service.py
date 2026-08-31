from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import (
    CLASSIFICATIONS,
    allowed_classifications,
    can_view_classification,
    has_secret_clearance,
)
from app.core.uploads import SavedFile, delete_upload
from app.models.post import Post
from app.models.user import User
from app.repositories import post_repository
from app.schemas.post import PostCreate, PostOut, PostReview

APPROVED = "da_duyet"
PENDING = "cho_duyet"
RETURNED = "tra_lai"


def _to_out(post: Post) -> PostOut:
    return PostOut(
        id=post.id,
        title=post.title,
        category=post.category,
        content=post.content,
        cover_image_url=post.cover_image_url,
        classification=post.classification,
        is_featured=post.is_featured,
        status=post.status,
        review_note=post.review_note,
        reviewed_by_id=post.reviewed_by_id,
        reviewed_at=post.reviewed_at,
        author_id=post.author_id,
        author_full_name=post.author.full_name,
        created_at=post.created_at,
    )


def _can_see(post: Post, user: Optional[User]) -> bool:
    is_author = user is not None and post.author_id == user.id
    is_commander = user is not None and user.role == "commander"
    if not (post.status == APPROVED or is_author or is_commander):
        return False
    return can_view_classification(post.classification, user) or is_author or is_commander


def _guard_secret_content(classification: str, current_user: User) -> None:
    if classification == "mat" and not has_secret_clearance(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chỉ huy hoặc người được cấp quyền MẬT mới được tạo nội dung mật",
        )


def create_post(db: Session, post_in: PostCreate, current_user: User) -> PostOut:
    _guard_secret_content(post_in.classification, current_user)
    initial = APPROVED if current_user.role == "commander" else PENDING
    post = post_repository.create(db, post_in, author_id=current_user.id, status=initial)
    return _to_out(post)


def list_posts(
    db: Session,
    current_user: Optional[User],
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    classification: Optional[str] = None,
) -> list[PostOut]:
    # Bac phan loai duoc phep xem, giao voi bac loc (neu co) tren URL.
    classes = allowed_classifications(current_user)
    if classification is not None:
        if classification not in CLASSIFICATIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Bậc phân loại không hợp lệ. Cho phép: {', '.join(CLASSIFICATIONS)}",
            )
        classes = [classification] if classification in classes else []

    if current_user is None or current_user.role == "soldier":
        posts = post_repository.list_all(
            db, skip=skip, limit=limit, category=category, statuses=[APPROVED], classifications=classes
        )
    elif current_user.role == "officer":
        posts = post_repository.list_for_author(
            db,
            author_id=current_user.id,
            skip=skip,
            limit=limit,
            category=category,
            also_status=APPROVED,
            classifications=classes,
        )
    else:  # commander -> xem tat ca (van ton trong bac loc classification neu co)
        statuses = [status_filter] if status_filter else None
        posts = post_repository.list_all(
            db, skip=skip, limit=limit, category=category, statuses=statuses, classifications=classes
        )
    return [_to_out(p) for p in posts]


def list_featured_public(db: Session, limit: int = 6) -> list[PostOut]:
    posts = post_repository.list_all(
        db,
        skip=0,
        limit=limit,
        statuses=[APPROVED],
        classifications=["cong_khai"],
        featured_only=True,
    )
    if not posts:
        posts = post_repository.list_all(
            db, skip=0, limit=limit, statuses=[APPROVED], classifications=["cong_khai"]
        )
    return [_to_out(p) for p in posts]


def get_post_or_404(db: Session, post_id: int, current_user: Optional[User]) -> PostOut:
    post = post_repository.get_with_author(db, post_id)
    if post is None or not _can_see(post, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return _to_out(post)


def _get_owned_or_404(db: Session, post_id: int, current_user: User) -> Post:
    post = post_repository.get_with_author(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if current_user.role != "commander" and post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return post


def update_post(db: Session, post_id: int, post_in: PostCreate, current_user: User) -> PostOut:
    post = _get_owned_or_404(db, post_id, current_user)
    _guard_secret_content(post_in.classification, current_user)
    updated = post_repository.update(db, post, post_in)
    # Officer sua bai -> quay lai hang cho duyet; commander sua giu nguyen trang thai.
    if current_user.role != "commander" and updated.status != PENDING:
        updated.status = PENDING
        updated.review_note = None
        updated.reviewed_by_id = None
        updated.reviewed_at = None
        updated = post_repository.save(db, updated)
    return _to_out(updated)


def review_post(db: Session, post_id: int, review_in: PostReview, current_user: User) -> PostOut:
    post = post_repository.get_with_author(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    reviewed = post_repository.set_review(
        db,
        post,
        status=review_in.status,
        review_note=review_in.review_note,
        reviewer_id=current_user.id,
    )
    return _to_out(reviewed)


def set_thumbnail(db: Session, post_id: int, saved: SavedFile, current_user: User) -> PostOut:
    post = _get_owned_or_404(db, post_id, current_user)
    old_url = post.cover_image_url
    post.cover_image_url = saved.url
    updated = post_repository.save(db, post)
    if old_url and old_url != saved.url:
        delete_upload(old_url)
    return _to_out(updated)


def delete_post(db: Session, post_id: int, current_user: User) -> None:
    post = _get_owned_or_404(db, post_id, current_user)
    cover = post.cover_image_url
    post_repository.delete(db, post)
    delete_upload(cover)
