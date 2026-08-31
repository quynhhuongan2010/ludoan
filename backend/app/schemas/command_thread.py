from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CommandThreadCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class CommandThreadCloseUpdate(BaseModel):
    is_closed: bool


class CommandMessageOut(BaseModel):
    id: int
    thread_id: int
    sender_id: int
    sender_full_name: str
    body: str
    attachment_url: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommandThreadOut(BaseModel):
    id: int
    title: str
    classification: str
    created_by_id: int
    created_by_full_name: str
    created_at: datetime
    last_message_at: Optional[datetime]
    is_closed: bool
    message_count: int
    unread_count: int

    model_config = ConfigDict(from_attributes=True)


class CommandThreadDetailOut(CommandThreadOut):
    messages: list[CommandMessageOut]
