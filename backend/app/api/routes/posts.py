from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user, require_roles
from app.core.database import get_db
from app.core.uploads import IMAGE_EXTENSIONS, save_upload
from app.models.user import User
from app.schemas.post import PostCreate, PostOut, PostReview
from app.services import post_service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post(
    "",
    response_model=PostOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def create_post(post_in: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return post_service.create_post(db, post_in, current_user)


@router.get("", response_model=list[PostOut], status_code=status.HTTP_200_OK)
def list_posts(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    classification: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return post_service.list_posts(
        db, current_user, skip, limit, category, status_filter, classification
    )


@router.get("/{post_id}", response_model=PostOut, status_code=status.HTTP_200_OK)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return post_service.get_post_or_404(db, post_id, current_user)


@router.put(
    "/{post_id}",
    response_model=PostOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def update_post(
    post_id: int,
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.update_post(db, post_id, post_in, current_user)


@router.post(
    "/{post_id}/review",
    response_model=PostOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("commander"))],
)
def review_post(
    post_id: int,
    review_in: PostReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.review_post(db, post_id, review_in, current_user)


@router.post(
    "/{post_id}/thumbnail",
    response_model=PostOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def upload_thumbnail(
    post_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = save_upload(file, subdir="posts", allowed_ext=IMAGE_EXTENSIONS)
    return post_service.set_thumbnail(db, post_id, saved, current_user)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post_service.delete_post(db, post_id, current_user)
    return None
