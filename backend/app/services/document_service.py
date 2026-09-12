from pathlib import Path
from typing import Optional, get_args

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.access import allowed_classifications, can_view_classification, has_secret_clearance
from app.core.roles import can_manage_documents
from app.core.config import settings
from app.core.uploads import DOCUMENT_EXTENSIONS, delete_upload, save_upload
from app.models.document import Document
from app.models.user import User
from app.repositories import document_repository
from app.schemas.common import Classification
from app.schemas.document import DocumentCategory, DocumentOut

VALID_CATEGORIES = set(get_args(DocumentCategory))
VALID_CLASSIFICATIONS = set(get_args(Classification))


def _to_out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        description=doc.description,
        category=doc.category,
        file_url=doc.file_url,
        file_name=doc.file_name,
        file_size=doc.file_size,
        content_type=doc.content_type,
        classification=doc.classification,
        uploaded_by_id=doc.uploaded_by_id,
        uploaded_by_full_name=doc.uploaded_by.full_name,
        created_at=doc.created_at,
    )


def _validate(category: str, classification: str, current_user: User) -> None:
    if not can_manage_documents(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Quản trị hệ thống, Lữ trưởng/Chính uỷ, Lữ phó/Phó chính uỷ mới được quản lý Văn bản – Tài liệu",
        )
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Chuyên mục không hợp lệ. Cho phép: {', '.join(sorted(VALID_CATEGORIES))}",
        )
    if classification not in VALID_CLASSIFICATIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Bậc truy cập không hợp lệ. Cho phép: {', '.join(sorted(VALID_CLASSIFICATIONS))}",
        )
    if classification == "mat" and not has_secret_clearance(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chỉ huy hoặc người được cấp quyền MẬT mới được tạo tài liệu mật",
        )


def create_document(
    db: Session,
    *,
    title: str,
    description: Optional[str],
    category: str,
    classification: str,
    file: UploadFile,
    current_user: User,
) -> DocumentOut:
    _validate(category, classification, current_user)
    saved = save_upload(file, subdir="documents", allowed_ext=DOCUMENT_EXTENSIONS)
    doc = document_repository.create(
        db,
        title=title,
        description=description,
        category=category,
        classification=classification,
        file_url=saved.url,
        file_name=saved.original_name,
        file_size=saved.size,
        content_type=saved.content_type,
        uploaded_by_id=current_user.id,
    )
    return _to_out(doc)


def list_documents(
    db: Session,
    current_user: Optional[User],
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
) -> list[DocumentOut]:
    docs = document_repository.list_all(
        db,
        skip=skip,
        limit=limit,
        category=category,
        classifications=allowed_classifications(current_user),
    )
    return [_to_out(d) for d in docs]


def _get_visible_or_404(db: Session, doc_id: int, current_user: Optional[User]) -> Document:
    doc = document_repository.get_with_uploader(db, doc_id)
    if doc is None or not can_view_classification(doc.classification, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu")
    return doc


def get_document_or_404(db: Session, doc_id: int, current_user: Optional[User]) -> DocumentOut:
    return _to_out(_get_visible_or_404(db, doc_id, current_user))


def get_download_target(db: Session, doc_id: int, current_user: Optional[User]) -> tuple[Path, str, str]:
    doc = _get_visible_or_404(db, doc_id, current_user)
    rel = doc.file_url[len("/static/") :] if doc.file_url.startswith("/static/") else doc.file_url
    path = (settings.upload_path / rel).resolve()
    if settings.upload_path.resolve() not in path.parents or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File không tồn tại trên máy chủ")
    return path, doc.file_name, doc.content_type


def update_document(
    db: Session,
    doc_id: int,
    *,
    title: str,
    description: Optional[str],
    category: str,
    classification: str,
    file: Optional[UploadFile] = None,
    current_user: User,
) -> DocumentOut:
    _validate(category, classification, current_user)
    doc = document_repository.get_with_uploader(db, doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu")
    doc.title = title
    doc.description = description
    doc.category = category
    doc.classification = classification
    old_file_url: Optional[str] = None
    if file is not None and file.filename:
        saved = save_upload(file, subdir="documents", allowed_ext=DOCUMENT_EXTENSIONS)
        old_file_url = doc.file_url
        doc.file_url = saved.url
        doc.file_name = saved.original_name
        doc.file_size = saved.size
        doc.content_type = saved.content_type
    out = _to_out(document_repository.save(db, doc))
    if old_file_url and old_file_url != doc.file_url:
        delete_upload(old_file_url)
    return out


def delete_document(db: Session, doc_id: int, current_user: User) -> None:
    if not can_manage_documents(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Quản trị hệ thống, Lữ trưởng/Chính uỷ, Lữ phó/Phó chính uỷ mới được xoá Văn bản – Tài liệu",
        )
    doc = document_repository.get_with_uploader(db, doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu")
    file_url = doc.file_url
    document_repository.delete(db, doc)
    delete_upload(file_url)
