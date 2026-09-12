from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.roles import COMMAND_ROLES
from app.models.user import User
from app.schemas.contact import ContactBookOut, ContactPage
from app.services import contact_service as service

router = APIRouter(
    prefix="/contact-books",
    tags=["contacts"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[ContactBookOut], status_code=status.HTTP_200_OK)
def list_books(db: Session = Depends(get_db)):
    return service.list_books(db)


@router.post(
    "",
    response_model=ContactBookOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def import_book(
    name: str = Form(""),
    description: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File rỗng")
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File vượt quá giới hạn {settings.MAX_UPLOAD_MB} MB",
        )
    return service.import_book(
        db,
        current_user,
        name=name,
        description=description,
        filename=file.filename or "",
        data=data,
    )


@router.get("/{book_id}", response_model=ContactBookOut, status_code=status.HTTP_200_OK)
def get_book(book_id: int, db: Session = Depends(get_db)):
    return service.get_book(db, book_id)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_book(db, current_user, book_id)


@router.get(
    "/{book_id}/contacts", response_model=ContactPage, status_code=status.HTTP_200_OK
)
def list_contacts(
    book_id: int,
    q: Optional[str] = Query(None, description="Từ khoá tra cứu trên mọi trường"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return service.list_contacts(db, book_id, q=q, skip=skip, limit=limit)
