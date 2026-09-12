"""Endpoint upload file dung chung: POST /api/upload.

Dung cho cac truong hop khong gan voi mot module nghiep vu cu the (vd chen anh /
video minh hoa trong trinh soan thao noi dung Tin tuc, Giao duc chinh tri). Cac
module co san (documents, posts thumbnail, directive/command threads, meetings...)
van tu goi save_upload rieng.

Dinh dang: anh (.jpg .jpeg .png .webp .gif), video (.mp4 .webm .ogg .mov .m4v),
tai lieu (.pdf .doc .docx .xls .xlsx .ppt .pptx). Video co gioi han dung luong
rieng (settings.MAX_VIDEO_UPLOAD_MB), con lai theo settings.MAX_UPLOAD_MB.
"""

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import require_roles
from app.core.roles import CONTENT_ROLES
from app.schemas.upload import UploadOut
from app.services import upload_service

router = APIRouter(prefix="/api", tags=["upload"])


@router.post(
    "/upload",
    response_model=UploadOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def upload_file(file: UploadFile = File(...)):
    return upload_service.save_generic_upload(file)
