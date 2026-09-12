"""Nghiep vu upload file dung chung (anh + video + tai lieu) qua POST /api/upload.

Khong ghi bang DB nao - chi bao mot lop nghiep vu mong quanh helper
`app.core.uploads.save_upload` (validate dinh dang, gioi han dung luong, doi ten
file theo UUID, luu xuong storage/uploads/common/).

Anh + tai lieu: gioi han `settings.MAX_UPLOAD_MB`.
Video (chen giua bai Tin tuc / Giao duc chinh tri): gioi han rieng, lon hon,
`settings.MAX_VIDEO_UPLOAD_MB`.
"""

from fastapi import UploadFile

from app.core.config import settings
from app.core.uploads import (
    DOCUMENT_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    ext_of,
    save_upload,
)
from app.schemas.upload import UploadOut

# Thu muc con trong storage/uploads/ danh cho file upload chung (khong thuoc
# module nghiep vu cu the nao). Phuc vu qua /static/common/<uuid>.<ext>.
COMMON_SUBDIR = "common"

# Cho phep anh minh hoa, video, va tai lieu dinh kem.
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | DOCUMENT_EXTENSIONS


def save_generic_upload(file: UploadFile) -> UploadOut:
    is_video = ext_of(file.filename or "") in VIDEO_EXTENSIONS
    max_mb = settings.MAX_VIDEO_UPLOAD_MB if is_video else settings.MAX_UPLOAD_MB
    saved = save_upload(file, COMMON_SUBDIR, ALLOWED_EXTENSIONS, max_mb=max_mb)
    return UploadOut(status="success", filename=saved.stored_name, url=saved.url)
