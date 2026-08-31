from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Classification

DocumentCategory = Literal[
    "bieu_mau",
    "huong_dan",
    "quy_che_quy_dinh",
    "ke_hoach",
    "bao_cao",
    "van_ban_chi_dao",
]


class DocumentMetaUpdate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: DocumentCategory
    classification: Classification = "noi_bo"


class DocumentOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: DocumentCategory
    file_url: str
    file_name: str
    file_size: int
    content_type: str
    classification: Classification
    uploaded_by_id: int
    uploaded_by_full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
