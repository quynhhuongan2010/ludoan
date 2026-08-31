from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DutyScheduleCreate(BaseModel):
    duty_date: date
    shift: str = Field(..., max_length=50)
    duty_officer: str = Field(..., max_length=100)
    role_title: str = Field(..., max_length=100)
    note: Optional[str] = Field(None, max_length=500)


class DutyScheduleOut(BaseModel):
    id: int
    duty_date: date
    shift: str
    duty_officer: str
    role_title: str
    note: Optional[str]
    author_id: int
    author_full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
