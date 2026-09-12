from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DocVisibility = Literal["chung", "rieng"]


class CommandThreadCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    # Thanh phan duoc gan ngay khi tao luong (nguoi tao luon tu dong duoc them).
    member_user_ids: list[int] = Field(default_factory=list)


class CommandThreadCloseUpdate(BaseModel):
    is_closed: bool


class MemberAddRequest(BaseModel):
    user_ids: list[int] = Field(..., min_length=1)


class MemberOut(BaseModel):
    user_id: int
    full_name: str
    unit_name: Optional[str] = None
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    member_count: int

    model_config = ConfigDict(from_attributes=True)


class CommandThreadDetailOut(CommandThreadOut):
    messages: list[CommandMessageOut]
    members: list[MemberOut]


class CommandThreadDocumentOut(BaseModel):
    id: int
    thread_id: int
    title: str
    visibility: DocVisibility
    file_url: str
    file_name: str
    file_size: int
    content_type: Optional[str]
    uploaded_by_id: int
    uploaded_by_full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommandThreadMinutesOut(BaseModel):
    id: int
    thread_id: int
    content: str
    message_count: int
    generated_by_id: int
    generated_by_full_name: str
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
