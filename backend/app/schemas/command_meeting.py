from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MeetingStatus = Literal["sap_dien_ra", "dang_dien_ra", "da_ket_thuc", "da_huy"]
AttendanceStatus = Literal["co_mat", "vang_mat", "chua_diem_danh"]


class CommandMeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = Field(default=None, max_length=255)
    meeting_link: Optional[str] = Field(default=None, max_length=500)
    agenda: Optional[str] = None
    attendee_user_ids: list[int] = Field(default_factory=list)


class CommandMeetingUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = Field(default=None, max_length=255)
    meeting_link: Optional[str] = Field(default=None, max_length=500)
    agenda: Optional[str] = None
    status: MeetingStatus = "sap_dien_ra"


class MinutesRequest(BaseModel):
    minutes: str = Field(..., min_length=1)
    mark_finished: bool = False


class InviteRequest(BaseModel):
    user_ids: list[int] = Field(..., min_length=1)


class AttendanceUpdate(BaseModel):
    attendance: Optional[AttendanceStatus] = None
    absence_reason: Optional[str] = Field(default=None, max_length=500)
    contribution_note: Optional[str] = None


class AttendeeOut(BaseModel):
    id: int
    meeting_id: int
    user_id: int
    full_name: str
    unit_id: Optional[int]
    unit_name: Optional[str]
    attendance: AttendanceStatus
    absence_reason: Optional[str]
    contribution_note: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class CommandMeetingOut(BaseModel):
    id: int
    title: str
    start_time: datetime
    end_time: Optional[datetime]
    location: Optional[str]
    meeting_link: Optional[str]
    agenda: Optional[str]
    minutes: Optional[str]
    attachment_url: Optional[str]
    attachment_name: Optional[str]
    status: MeetingStatus
    classification: str
    created_by_id: int
    created_by_full_name: str
    created_at: datetime
    attendee_count: int
    present_count: int
    my_attendance: Optional[AttendanceStatus]

    model_config = ConfigDict(from_attributes=True)


class CommandMeetingDetailOut(CommandMeetingOut):
    attendees: list[AttendeeOut]
