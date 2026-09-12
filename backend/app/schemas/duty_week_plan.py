from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.duty_plan_attachment import DutyPlanAttachmentOut
from app.schemas.duty_schedule import DutyScheduleOut


class DutyWeekPlanCreate(BaseModel):
    unit_id: int
    # Ngay bat ky trong tuan can lap; server chuan hoa ve Thu Hai (ISO).
    week_start: date
    note: Optional[str] = Field(None, max_length=500)


class DutyWeekPlanUpdate(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


class DutyWeekPlanReview(BaseModel):
    status: Literal["da_duyet", "tra_lai"]
    review_note: Optional[str] = Field(None, max_length=500)


class DutyWeekPlanOut(BaseModel):
    id: int
    unit_id: int
    unit_name: str
    week_start: date
    week_end: date
    week_label: str  # VD "Tuần 36/2026"
    status: str
    status_label: str
    note: Optional[str]
    entry_count: int
    attachment_count: int
    personnel_present: int
    personnel_total: int
    submitted_by_id: Optional[int]
    submitted_by_name: Optional[str]
    submitted_at: Optional[datetime]
    reviewed_by_id: Optional[int]
    reviewed_by_name: Optional[str]
    reviewed_at: Optional[datetime]
    review_note: Optional[str]
    author_id: int
    author_full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DutyWeekPlanDetail(DutyWeekPlanOut):
    entries: list[DutyScheduleOut]
    attachments: list[DutyPlanAttachmentOut] = []
