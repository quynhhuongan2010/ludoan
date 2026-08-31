from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

EducationCategory = Literal[
    "hoc_tap_chinh_tri_quan_su",
    "tuyen_truyen",
    "phap_luat_bien_gioi",
    "lich_su_truyen_thong",
]


class EducationMaterialCreate(BaseModel):
    title: str = Field(..., max_length=255)
    category: EducationCategory
    period_label: Optional[str] = Field(None, max_length=50)
    content: str
    attachment_url: Optional[str] = Field(None, max_length=500)


class EducationMaterialOut(BaseModel):
    id: int
    title: str
    category: EducationCategory
    period_label: Optional[str]
    content: str
    attachment_url: Optional[str]
    author_id: int
    author_full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
