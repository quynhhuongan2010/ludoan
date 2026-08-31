from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DirectiveThreadCreate(BaseModel):
    # BCH/admin chon don vi bat ky; tai khoan don vi bi ep ve don vi cua minh.
    unit_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)


class ThreadCloseUpdate(BaseModel):
    is_closed: bool


class DirectiveMessageOut(BaseModel):
    id: int
    thread_id: int
    sender_id: int
    sender_full_name: str
    body: str
    attachment_url: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DirectiveThreadOut(BaseModel):
    id: int
    unit_id: int
    unit_name: str
    title: str
    created_by_id: int
    created_by_full_name: str
    created_at: datetime
    last_message_at: Optional[datetime]
    is_closed: bool
    message_count: int
    unread_count: int

    model_config = ConfigDict(from_attributes=True)


class DirectiveThreadDetailOut(DirectiveThreadOut):
    messages: list[DirectiveMessageOut]
