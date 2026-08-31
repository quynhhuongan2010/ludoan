from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Classification

PostCategory = Literal["huan_luyen", "dan_van", "khen_thuong", "guong_nguoi_tot"]
PostStatus = Literal["cho_duyet", "da_duyet", "tra_lai"]


class PostCreate(BaseModel):
    title: str = Field(..., max_length=255)
    category: PostCategory
    content: str
    cover_image_url: Optional[str] = Field(None, max_length=500)
    classification: Classification = "noi_bo"
    is_featured: bool = False


class PostReview(BaseModel):
    # da_duyet = duyet dang; tra_lai = tra ve cho tac gia sua
    status: Literal["da_duyet", "tra_lai"]
    review_note: Optional[str] = Field(None, max_length=500)


class PostOut(BaseModel):
    id: int
    title: str
    category: PostCategory
    content: str
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
