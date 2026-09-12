from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import Classification

PostCategory = Literal[
    "huan_luyen",
    "dan_van",
    "khen_thuong",
    "guong_nguoi_tot",
    "hoat_dong_don_vi",
    "cong_tac_dang",
    "thong_tin_lien_lac",
    "su_kien_le_ky_niem",
]
# nhap = ban nhap (chua gui duyet); cho_duyet -> da_duyet / tra_lai
PostStatus = Literal["nhap", "cho_duyet", "da_duyet", "tra_lai"]

MAX_TAGS = 20
MAX_TAG_LEN = 40


class PostCreate(BaseModel):
    title: str = Field(..., max_length=255)
    summary: Optional[str] = Field(None, max_length=500)
    # De trong -> backend tu sinh tu title (bo dau tieng Viet). Bi trung -> them hau to.
    slug: Optional[str] = Field(None, max_length=255)
    category: PostCategory
    content: str
    tags: list[str] = Field(default_factory=list)
    cover_image_url: Optional[str] = Field(None, max_length=500)
    classification: Classification = "noi_bo"
    is_featured: bool = False

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, raw: list[str]) -> list[str]:
        seen: list[str] = []
        for tag in raw:
            t = (tag or "").strip()[:MAX_TAG_LEN]
            if t and t.lower() not in {s.lower() for s in seen}:
                seen.append(t)
        return seen[:MAX_TAGS]


class PostReview(BaseModel):
    # da_duyet = duyet dang; tra_lai = tra ve cho tac gia sua
    status: Literal["da_duyet", "tra_lai"]
    review_note: Optional[str] = Field(None, max_length=500)


class PostOut(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    slug: Optional[str]
    category: PostCategory
    content: str
    tags: list[str]
    cover_image_url: Optional[str]
    classification: Classification
    is_featured: bool
    status: PostStatus
    review_note: Optional[str]
    reviewed_by_id: Optional[int]
    reviewed_at: Optional[datetime]
    author_id: int
    author_full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
