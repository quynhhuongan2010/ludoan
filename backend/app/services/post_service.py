import re
import unicodedata
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import (
    CLASSIFICATIONS,
    allowed_classifications,
    can_view_classification,
    has_secret_clearance,
)
from app.core.roles import is_command
from app.core.uploads import SavedFile, delete_upload
from app.models.post import Post
from app.models.user import User
from app.repositories import post_repository
from app.schemas.post import PostCreate, PostOut, PostReview

APPROVED = "da_duyet"
PENDING = "cho_duyet"
RETURNED = "tra_lai"
DRAFT = "nhap"

_VN_MAP = str.maketrans(
    "àáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ",
    "aaaaaaaaaaaaaaaaadeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyy",
)


def _slugify(text: str) -> str:
    lowered = (text or "").strip().lower().translate(_VN_MAP)
    ascii_only = unicodedata.normalize("NFKD", lowered).encode("ascii", "ignore").decode()
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", ascii_only)).strip("-")


_CONTENT_IMG_RE = re.compile(r"<img[^>]+?src=[\"']([^\"']+)[\"']", re.IGNORECASE)


def _first_content_image(content: Optional[str]) -> Optional[str]:
    """Anh minh hoa suy ra tu noi dung bai: lay <img> dau tien tro toi tep da tai
    len server noi bo (`/static/...`). Dung lam anh bia khi tac gia CHUA chon anh
    bia rieng — khong luu xuong DB, tinh lai moi lan doc nen luon khop noi dung.
    """
    if not content:
        return None
    for raw in _CONTENT_IMG_RE.findall(content):
        idx = (raw or "").find("/static/")
        if idx != -1:
            return raw[idx:]  # ve dang tuong doi /static/... cho dong bo voi cover_image_url
    return None


def _resolve_slug(db: Session, raw: Optional[str], fallback_title: str, exclude_id: Optional[int]) -> str:
    base = _slugify(raw or "") or _slugify(fallback_title) or "bai-viet"
    candidate = base
    suffix = 2
    while post_repository.slug_taken(db, candidate, exclude_id=exclude_id):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _to_out(post: Post) -> PostOut:
    return PostOut(
        id=post.id,
        title=post.title,
        summary=post.summary,
        slug=post.slug,
        category=post.category,
        content=post.content,
        tags=post.tags or [],
        # Anh bia tac gia chon; neu bo trong -> tu lay anh dau tien trong noi dung.
        cover_image_url=post.cover_image_url or _first_content_image(post.content),
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
    is_commander = is_command(user)
    if not (post.status == APPROVED or is_author or is_commander):
        return False
    return can_view_classification(post.classification, user) or is_author or is_commander


def _guard_secret_content(classification: str, current_user: User) -> None:
    if classification == "mat" and not has_secret_clearance(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chỉ huy hoặc người được cấp quyền MẬT mới được tạo nội dung mật",
        )


def create_post(
    db: Session, post_in: PostCreate, current_user: User, as_draft: bool = False
) -> PostOut:
    _guard_secret_content(post_in.classification, current_user)
    if as_draft:
        initial = DRAFT
    else:
        initial = APPROVED if is_command(current_user) else PENDING
    post_in = post_in.model_copy(
        update={"slug": _resolve_slug(db, post_in.slug, post_in.title, exclude_id=None)}
    )
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

    if current_user is None:
        posts = post_repository.list_all(
            db, skip=skip, limit=limit, category=category, statuses=[APPROVED], classifications=classes
        )
    elif not is_command(current_user):
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài viết")
    return _to_out(post)


def _get_owned_or_404(db: Session, post_id: int, current_user: User) -> Post:
    post = post_repository.get_with_author(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài viết")
    if not is_command(current_user) and post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không đủ quyền thực hiện thao tác này")
    return post


def update_post(
    db: Session, post_id: int, post_in: PostCreate, current_user: User, as_draft: bool = False
) -> PostOut:
    post = _get_owned_or_404(db, post_id, current_user)
    _guard_secret_content(post_in.classification, current_user)
    was_draft = post.status == DRAFT
    post_in = post_in.model_copy(
        update={"slug": _resolve_slug(db, post_in.slug, post_in.title, exclude_id=post_id)}
    )
    updated = post_repository.update(db, post, post_in)
    if as_draft:
        # Giu / dua ve ban nhap - khong day vao hang duyet.
        if updated.status != DRAFT:
            updated = post_repository.set_status(db, updated, status=DRAFT, clear_review=True)
    elif was_draft:
        # Roi ban nhap -> gui duyet (chi huy: dang luon).
        target = APPROVED if is_command(current_user) else PENDING
        updated = post_repository.set_status(db, updated, status=target, clear_review=True)
    elif not is_command(current_user) and updated.status != PENDING:
        # Vai tro khong phai chi huy sua bai da duyet/tra lai -> quay lai hang cho duyet.
        updated = post_repository.set_status(db, updated, status=PENDING, clear_review=True)
    return _to_out(updated)


def submit_post(db: Session, post_id: int, current_user: User) -> PostOut:
    post = _get_owned_or_404(db, post_id, current_user)
    if post.status not in (DRAFT, RETURNED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chỉ gửi duyệt được bài ở trạng thái nháp hoặc bị trả lại",
        )
    target = APPROVED if is_command(current_user) else PENDING
    return _to_out(post_repository.set_status(db, post, status=target, clear_review=True))


def review_post(db: Session, post_id: int, review_in: PostReview, current_user: User) -> PostOut:
    post = post_repository.get_with_author(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài viết")
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
