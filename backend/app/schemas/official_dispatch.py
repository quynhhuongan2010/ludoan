from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DispatchDirection = Literal["di", "den"]
DispatchStatus = Literal["moi", "dang_xu_ly", "da_xu_ly", "luu_tru"]


class DispatchUpdate(BaseModel):
    direction: DispatchDirection
    dispatch_number: str = Field(..., min_length=1, max_length=80)
    summary: str = Field(..., min_length=1, max_length=500)
    issuing_org: Optional[str] = Field(default=None, max_length=200)
    receiving_org: Optional[str] = Field(default=None, max_length=200)
    issued_date: Optional[date] = None
    received_date: Optional[date] = None
    status: DispatchStatus = "moi"
    note: Optional[str] = None


class AcknowledgeRequest(BaseModel):
    response_note: Optional[str] = Field(default=None, max_length=500)


class DispatchAckOut(BaseModel):
    user_id: int
    full_name: str
    role: str
    acknowledged_at: Optional[datetime] = None
    response_note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OfficialDispatchOut(BaseModel):
    id: int
    direction: DispatchDirection
    dispatch_number: str
    summary: str
    issuing_org: Optional[str]
    receiving_org: Optional[str]
    issued_date: Optional[date]
    received_date: Optional[date]
    status: DispatchStatus
    classification: str
    note: Optional[str]
    attachment_url: Optional[str]
    attachment_name: Optional[str]
    created_by_id: int
    created_by_full_name: str
    created_at: datetime
    recipient_count: int
    acknowledged_count: int
    acknowledged_by_me: bool

    model_config = ConfigDict(from_attributes=True)


class OfficialDispatchDetailOut(OfficialDispatchOut):
    acknowledged: list[DispatchAckOut]
    pending: list[DispatchAckOut]
