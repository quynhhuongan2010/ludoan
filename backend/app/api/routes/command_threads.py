from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.uploads import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, save_upload
from app.models.user import User
from app.schemas.command_thread import (
    CommandMessageOut,
    CommandThreadCloseUpdate,
    CommandThreadCreate,
    CommandThreadDetailOut,
    CommandThreadOut,
)
from app.services import command_thread_service as service

router = APIRouter(
    prefix="/command-threads",
    tags=["command-threads"],
    dependencies=[Depends(get_current_user)],
)

_ATTACH_EXT = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS


@router.get("", response_model=list[CommandThreadOut], status_code=status.HTTP_200_OK)
def list_threads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_threads(db, current_user, skip=skip, limit=limit)


@router.post("", response_model=CommandThreadOut, status_code=status.HTTP_201_CREATED)
def create_thread(
    payload: CommandThreadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_thread(db, current_user, payload)


@router.get(
    "/{thread_id}", response_model=CommandThreadDetailOut, status_code=status.HTTP_200_OK
)
def get_thread(
    thread_id: int,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_thread_detail(db, current_user, thread_id, skip=skip, limit=limit)


@router.post(
    "/{thread_id}/messages",
    response_model=CommandMessageOut,
    status_code=status.HTTP_201_CREATED,
)
def post_message(
    thread_id: int,
    body: str = Form(""),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = (
        save_upload(file, subdir="command", allowed_ext=_ATTACH_EXT)
        if file is not None
        else None
    )
    return service.post_message(db, current_user, thread_id, body, saved)


@router.patch(
    "/{thread_id}/close", response_model=CommandThreadOut, status_code=status.HTTP_200_OK
)
def close_thread(
    thread_id: int,
    payload: CommandThreadCloseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.set_closed(db, current_user, thread_id, payload.is_closed)
