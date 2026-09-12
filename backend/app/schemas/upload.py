from typing import Literal

from pydantic import BaseModel


class UploadOut(BaseModel):
    """Ket qua tra ve cho POST /api/upload (upload file dung chung)."""

    status: Literal["success"] = "success"
    filename: str  # ten file da luu tren dia (dang <uuid>.<ext>)
    url: str  # duong dan phuc vu qua /static, vd /static/common/<uuid>.jpg
