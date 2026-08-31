from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AnnouncementPriority = Literal["thap", "binh_thuong", "cao", "khan"]


class AnnouncementCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    priority: AnnouncementPriority = "binh_thuong"
    is_pinned: bool = False
    is_public: bool = False
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str
    priority: AnnouncementPriority
    is_pinned: bool
    is_public: bool
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    author_id: int
    author_full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
