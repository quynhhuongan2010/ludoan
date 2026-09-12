from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.uploads import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, save_secure_upload
from app.models.user import User
from app.schemas.command_thread import (
    CommandMessageOut,
    CommandThreadCloseUpdate,
    CommandThreadCreate,
    CommandThreadDetailOut,
    CommandThreadDocumentOut,
    CommandThreadMinutesOut,
    CommandThreadOut,
    DocVisibility,
    MemberAddRequest,
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
        save_secure_upload(file, subdir="command_messages", allowed_ext=_ATTACH_EXT)
        if file is not None
        else None
    )
    return service.post_message(db, current_user, thread_id, body, saved)


@router.get("/{thread_id}/messages/{message_id}/download")
def download_message_attachment(
    thread_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path, filename, content_type = service.get_message_attachment_download_target(
        db, current_user, thread_id, message_id
    )
    return FileResponse(path, filename=filename, media_type=content_type)


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


# --------------------------------------------------------------------- thanh phan (members)


@router.post(
    "/{thread_id}/members",
    response_model=CommandThreadDetailOut,
    status_code=status.HTTP_201_CREATED,
)
def add_members(
    thread_id: int,
    payload: MemberAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.add_members(db, current_user, thread_id, payload.user_ids)


@router.delete("/{thread_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    thread_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.remove_member(db, current_user, thread_id, user_id)


# --------------------------------------------------------------------- kho van ban


@router.get(
    "/{thread_id}/documents",
    response_model=list[CommandThreadDocumentOut],
    status_code=status.HTTP_200_OK,
)
def list_documents(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_documents(db, current_user, thread_id)


@router.post(
    "/{thread_id}/documents",
    response_model=CommandThreadDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    thread_id: int,
    title: str = Form(""),
    visibility: DocVisibility = Form("chung"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = save_secure_upload(file, subdir="command_docs", allowed_ext=_ATTACH_EXT)
    return service.upload_document(db, current_user, thread_id, title, visibility, saved)


@router.get("/{thread_id}/documents/{doc_id}/download")
def download_document(
    thread_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path, filename, content_type = service.get_download_target(
        db, current_user, thread_id, doc_id
    )
    return FileResponse(path, filename=filename, media_type=content_type)


@router.delete("/{thread_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document(
    thread_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.remove_document(db, current_user, thread_id, doc_id)


# --------------------------------------------------------------------- bien ban (minutes)


@router.post(
    "/{thread_id}/minutes/generate",
    response_model=CommandThreadMinutesOut,
    status_code=status.HTTP_201_CREATED,
)
def generate_minutes(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.generate_minutes(db, current_user, thread_id)


@router.get(
    "/{thread_id}/minutes",
    response_model=list[CommandThreadMinutesOut],
    status_code=status.HTTP_200_OK,
)
def list_minutes(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_minutes(db, current_user, thread_id)
