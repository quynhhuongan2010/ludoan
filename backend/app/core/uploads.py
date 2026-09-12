"""Ho tro luu file upload xuong dia + tra ve URL phuc vu qua /static hoac /secure.
Tich hop kiem tra chu ky nhi phan (Magic Bytes), chan ma doc/web shell, lam sach ten file
va kiem tra dung luong o dia an toan (Step 4 - v7.4.0).
"""

import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
# Video chen giua bai viet (Tin tuc / Giao duc chinh tri). .mov tu dien thoai
# hay gap; trinh duyet phat .mp4/.webm/.ogg truc tiep, .mov tuy trinh duyet.
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov", ".m4v"}
# Tep nen (gui kem trong chat / tai lieu). Kiem tra chu ky nhi phan o
# validate_magic_bytes ben duoi. `.tar.gz` -> suffix la `.gz` (da co).
ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"}

# Danh sach chu ky/mau ma doc va web shell nguy hiem
DANGEROUS_PATTERNS = [
    b"<?php",
    b"<?=",
    b"#!/bin/sh",
    b"#!/bin/bash",
    b"#!/usr/bin",
    b"<script",
    b"<%",
]


@dataclass
class SavedFile:
    url: str
    stored_name: str
    original_name: str
    size: int
    content_type: str


def _ext(filename: str) -> str:
    return Path(filename or "").suffix.lower()


# Alias cong khai (dung o service khac de nhan dien loai file truoc khi luu).
ext_of = _ext


def sanitize_filename(filename: str) -> str:
    """Loai bo duong dan nguy hiem (path traversal), null byte va ky tu dieu khien."""
    if not filename:
        return "file"
    # Lay ten co ban (loai bo ../ hoac ..\\)
    base = Path(filename).name.replace("\x00", "").strip()
    # Loai bo cac ky tu dieu khien
    base = re.sub(r"[\r\n\t]", "", base)
    return base if base else "file"


def check_disk_space(target_dir: Path, incoming_bytes: int) -> None:
    """Kiem tra dung luong o dia con lai truoc khi ghi file."""
    try:
        usage = shutil.disk_usage(target_dir)
        min_free_bytes = settings.MIN_FREE_DISK_MB * 1024 * 1024
        if usage.free - incoming_bytes < min_free_bytes:
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail="Dung lượng lưu trữ máy chủ sắp đầy, không thể tiếp nhận tệp tải lên mới.",
            )
    except OSError:
        pass


def validate_magic_bytes(ext: str, data: bytes) -> None:
    """Kiem tra chu ky nhi phan va chan ma thuc thi doc hai."""
    # 1. Chan tuyet doi cac chu ky ma thuc thi
    if data.startswith(b"MZ"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp bị từ chối: Phát hiện chữ ký tệp thực thi Windows (MZ/PE) nguy hiểm.",
        )
    if data.startswith(b"\x7fELF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp bị từ chối: Phát hiện chữ ký tệp thực thi Linux (ELF) nguy hiểm.",
        )
    if data.startswith(b"\xca\xfe\xba\xbe"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tệp bị từ chối: Phát hiện chữ ký bytecode Java Class nguy hiểm.",
        )

    # Quet web shell / script trong phan dau tep (2048 bytes)
    header_lower = data[:2048].lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in header_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp bị từ chối: Phát hiện mã script hoặc web shell độc hại trong nội dung tệp.",
            )

    # 2. Doi chieu chu ky theo tung dinh dang cho phep
    if ext == ".pdf":
        if not data.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp PDF không hợp lệ (thiếu chữ ký %PDF tiêu chuẩn).",
            )
    elif ext == ".png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp PNG không hợp lệ (thiếu chữ ký PNG tiêu chuẩn).",
            )
    elif ext in (".jpg", ".jpeg"):
        if not data.startswith(b"\xff\xd8\xff"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp JPEG/JPG không hợp lệ (thiếu chữ ký SOI tiêu chuẩn).",
            )
    elif ext == ".gif":
        if not (data.startswith(b"GIF87a") or data.startswith(b"GIF89a")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp GIF không hợp lệ (thiếu chữ ký GIF tiêu chuẩn).",
            )
    elif ext == ".webp":
        if not (data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp WebP không hợp lệ (thiếu chữ ký RIFF...WEBP tiêu chuẩn).",
            )
    elif ext in (".docx", ".xlsx", ".pptx"):
        # Office XML moi luon la container zip PK
        if not data.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tệp văn bản '{ext}' không hợp lệ (thiếu chữ ký container Office XML tiêu chuẩn).",
            )
    elif ext in (".doc", ".xls", ".ppt"):
        # Office cu OLE Compound File
        if not data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tệp văn bản '{ext}' không hợp lệ (thiếu chữ ký OLE Compound File tiêu chuẩn).",
            )
    elif ext in (".mp4", ".m4v", ".mov"):
        if len(data) >= 8:
            box_type = data[4:8]
            if box_type not in (b"ftyp", b"moov", b"wide", b"mdat", b"free", b"skip"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tệp video MP4/MOV không hợp lệ (thiếu container ISO-BMFF hợp lệ).",
                )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tệp video quá ngắn.")
    elif ext == ".webm":
        if not data.startswith(b"\x1a\x45\xdf\xa3"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp video WebM không hợp lệ (thiếu chữ ký EBML tiêu chuẩn).",
            )
    elif ext == ".ogg":
        if not data.startswith(b"OggS"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp video OGG không hợp lệ (thiếu chữ ký OggS tiêu chuẩn).",
            )
    elif ext == ".zip":
        # PK\x03\x04 (thuong), PK\x05\x06 (rong), PK\x07\x08 (spanned)
        if not data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp ZIP không hợp lệ (thiếu chữ ký PK tiêu chuẩn).",
            )
    elif ext == ".rar":
        if not data.startswith(b"Rar!\x1a\x07"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp RAR không hợp lệ (thiếu chữ ký Rar! tiêu chuẩn).",
            )
    elif ext == ".7z":
        if not data.startswith(b"7z\xbc\xaf\x27\x1c"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp 7z không hợp lệ (thiếu chữ ký 7z tiêu chuẩn).",
            )
    elif ext == ".gz":
        if not data.startswith(b"\x1f\x8b"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp GZIP (.gz/.tar.gz) không hợp lệ (thiếu chữ ký gzip tiêu chuẩn).",
            )
    elif ext == ".bz2":
        if not data.startswith(b"BZh"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp BZIP2 không hợp lệ (thiếu chữ ký BZh tiêu chuẩn).",
            )
    elif ext == ".tar":
        # tar khong co magic o offset 0; header POSIX co "ustar" o offset 257
        if len(data) >= 512 and data[257:262] not in (b"ustar",):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tệp TAR không hợp lệ (thiếu chữ ký ustar tiêu chuẩn).",
            )


def save_upload(
    file: UploadFile,
    subdir: str,
    allowed_ext: set[str],
    *,
    max_mb: int | None = None,
) -> SavedFile:
    original_name = sanitize_filename(file.filename or "file")
    ext = _ext(original_name)
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng '{ext or 'không rõ'}' không được phép. Cho phép: {', '.join(sorted(allowed_ext))}",
        )

    limit_mb = max_mb or settings.MAX_UPLOAD_MB
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File rỗng")

    max_bytes = limit_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File vượt quá giới hạn {limit_mb} MB",
        )

    # Kiem tra chu ky nhi phan & ma doc
    validate_magic_bytes(ext, data)

    target_dir = settings.upload_path / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    check_disk_space(target_dir, len(data))

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


def save_secure_upload(
    file: UploadFile,
    subdir: str,
    allowed_ext: set[str],
    *,
    max_mb: int | None = None,
) -> SavedFile:
    """Luu file bao mat (cong van mat, tai lieu mat) vao SECURE_UPLOAD_DIR.

    Tep nay TUYET DOI KHONG nam trong /static, khong the tai truc tiep qua URL
    tinh, bat buoc phai tai qua endpoint API co xac thuc JWT va kiem tra quyen MAT.
    """
    original_name = sanitize_filename(file.filename or "file")
    ext = _ext(original_name)
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng '{ext or 'không rõ'}' không được phép. Cho phép: {', '.join(sorted(allowed_ext))}",
        )

    limit_mb = max_mb or settings.MAX_UPLOAD_MB
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File rỗng")

    max_bytes = limit_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File vượt quá giới hạn {limit_mb} MB",
        )

    # Kiem tra chu ky nhi phan & ma doc
    validate_magic_bytes(ext, data)

    target_dir = settings.secure_upload_path / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    check_disk_space(target_dir, len(data))

    stored_name = f"{uuid.uuid4().hex}{ext}"
    (target_dir / stored_name).write_bytes(data)

    return SavedFile(
        url=f"/secure/{subdir}/{stored_name}",
        stored_name=stored_name,
        original_name=original_name,
        size=len(data),
        content_type=file.content_type or "application/octet-stream",
    )


def delete_secure_upload(url: str | None) -> None:
    """Xoa file vat ly tu duong dan /secure/<subdir>/<name> hoac file cu /static/command/..."""
    if not url:
        return
    if url.startswith("/secure/"):
        rel = url[len("/secure/") :]
        target = settings.secure_upload_path / rel
        try:
            if target.is_file() and settings.secure_upload_path in target.resolve().parents:
                target.unlink()
        except OSError:
            pass
    elif url.startswith("/static/"):
        # Tuong thich nguoc cho file cu tao truoc khi nang cap
        delete_upload(url)
