from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Classification

DirectiveStatus = Literal["nhap", "da_ban_hanh"]


class DirectiveCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    status: DirectiveStatus = "nhap"
    classification: Classification = "noi_bo"


class DirectiveOut(BaseModel):
    id: int
    title: str
    content: str
    status: DirectiveStatus
    classification: Classification
    author_id: int
    author_full_name: str
    created_at: datetime
    # thong ke muc do quan triet
    recipient_count: int
    acknowledged_count: int
    acknowledged_by_me: bool

    model_config = ConfigDict(from_attributes=True)


class DirectiveAckUser(BaseModel):
    user_id: int
    full_name: str
    role: int
    acknowledged_at: datetime | None = None


class DirectiveAckReport(BaseModel):
    directive_id: int
    recipient_count: int
    acknowledged_count: int
    acknowledged: list[DirectiveAckUser]
    pending: list[DirectiveAckUser]
