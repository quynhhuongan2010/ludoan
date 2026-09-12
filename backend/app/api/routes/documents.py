from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user, require_roles
from app.core.database import get_db
from app.core.roles import DOCUMENT_MANAGE_ROLES
from app.models.user import User
from app.schemas.document import DocumentOut
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*DOCUMENT_MANAGE_ROLES))],
)
def upload_document(
    title: str = Form(..., max_length=255),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    classification: str = Form("noi_bo"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return document_service.create_document(
        db,
        title=title,
        description=description,
        category=category,
        classification=classification,
        file=file,
        current_user=current_user,
    )


@router.get("", response_model=list[DocumentOut], status_code=status.HTTP_200_OK)
def list_documents(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return document_service.list_documents(db, current_user, skip, limit, category)


@router.get("/{doc_id}", response_model=DocumentOut, status_code=status.HTTP_200_OK)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return document_service.get_document_or_404(db, doc_id, current_user)


@router.get("/{doc_id}/download")
def download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    path, filename, content_type = document_service.get_download_target(db, doc_id, current_user)
    return FileResponse(path, filename=filename, media_type=content_type)


@router.put(
    "/{doc_id}",
    response_model=DocumentOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*DOCUMENT_MANAGE_ROLES))],
)
def update_document(
    doc_id: int,
    title: str = Form(..., max_length=255),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    classification: str = Form("noi_bo"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return document_service.update_document(
        db,
        doc_id,
        title=title,
        description=description,
        category=category,
        classification=classification,
        file=file,
        current_user=current_user,
    )


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*DOCUMENT_MANAGE_ROLES))],
)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document_service.delete_document(db, doc_id, current_user)
    return None
