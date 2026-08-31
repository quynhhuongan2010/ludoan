"""Ho tro luu file upload xuong dia + tra ve URL phuc vu qua /static."""

import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}


@dataclass
class SavedFile:
    url: str
    stored_name: str
    original_name: str
    size: int
    content_type: str


def _ext(filename: str) -> str:
    return Path(filename or "").suffix.lower()


def save_upload(file: UploadFile, subdir: str, allowed_ext: set[str]) -> SavedFile:
    original_name = file.filename or "file"
    ext = _ext(original_name)
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng '{ext or 'không rõ'}' không được phép. Cho phép: {', '.join(sorted(allowed_ext))}",
        )

    data = file.file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File vượt quá giới hạn {settings.MAX_UPLOAD_MB} MB",
        )
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File rỗng")

    target_dir = settings.upload_path / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    (target_dir / stored_name).write_bytes(data)

    return SavedFile(
        url=f"/static/{subdir}/{stored_name}",
        stored_name=stored_name,
        original_name=original_name,
        size=len(data),
        content_type=file.content_type or "application/octet-stream",
    )


def delete_upload(url: str | None) -> None:
    """Xoa file vat ly tu URL dang /static/<subdir>/<name>. Bo qua neu khong hop le."""
    if not url or not url.startswith("/static/"):
        return
    rel = url[len("/static/") :]
    target = settings.upload_path / rel
    try:
        if target.is_file() and settings.upload_path in target.resolve().parents:
            target.unlink()
    except OSError:
        pass
