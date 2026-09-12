from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# 7 nhom cuong vi truc co dinh (khop frontend/src/types/dutySchedule.ts).
DutyType = Literal[
    "truc_chi_huy",
    "truc_ban_tac_chien",
    "truc_ban_noi_vu",
    "truc_chuyen_mon",
    "truc_ca_kip",
    "truc_bao_ve",
    "khac",
]

DUTY_TYPE_LABELS: dict[str, str] = {
    "truc_chi_huy": "Trực chỉ huy",
    "truc_ban_tac_chien": "Trực ban tác chiến",
    "truc_ban_noi_vu": "Trực ban nội vụ",
    "truc_chuyen_mon": "Trực chuyên môn",
    "truc_ca_kip": "Trực ca kíp",
    "truc_bao_ve": "Trực bảo vệ / vệ binh",
    "khac": "Khác",
}

# Trang thai phe duyet bang truc tuan (giong luong duyet posts).
DutyPlanStatus = Literal["nhap", "cho_duyet", "da_duyet", "tra_lai"]

DUTY_PLAN_STATUS_LABELS: dict[str, str] = {
    "nhap": "Nháp",
    "cho_duyet": "Chờ duyệt",
    "da_duyet": "Đã duyệt",
    "tra_lai": "Trả lại",
}


def duty_type_label(value: str) -> str:
    return DUTY_TYPE_LABELS.get(value, value)


def duty_plan_status_label(value: str) -> str:
    return DUTY_PLAN_STATUS_LABELS.get(value, value)


class DutyScheduleCreate(BaseModel):
    """Mot dong ca truc. `unit_id` va tuan suy tu bang cha (DutyWeekPlan)."""

    duty_date: date
    duty_type: DutyType = "khac"
    shift: str = Field(..., max_length=50)
    duty_officer: str = Field(..., max_length=100)
    role_title: str = Field(..., max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=30)
    personnel_present: Optional[int] = Field(None, ge=0)
    personnel_total: Optional[int] = Field(None, ge=0)
    note: Optional[str] = Field(None, max_length=500)


class DutyScheduleOut(BaseModel):
    id: int
    week_plan_id: Optional[int]
    duty_date: date
    unit_id: Optional[int]
    unit_name: Optional[str]
    duty_type: str
    duty_type_label: str
    shift: str
    duty_officer: str
    role_title: str
    contact_phone: Optional[str]
    personnel_present: Optional[int]
    personnel_total: Optional[int]
    note: Optional[str]
    author_id: int
    author_full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Tinh nang 1: Kip truc toan Lu doan theo ngay (gom theo don vi) -----


class DutyUnitGroup(BaseModel):
    unit_id: Optional[int]
    unit_name: str
    plan_id: Optional[int]
    plan_status: Optional[str]
    plan_status_label: Optional[str]
    entries: list[DutyScheduleOut]
    entry_count: int
    personnel_present: int
    personnel_total: int


class DutyDayBoard(BaseModel):
    date: date
    weekday_label: str
    groups: list[DutyUnitGroup]
    total_entries: int
    personnel_present: int
    personnel_total: int


# ----- Tinh nang 2: Truc tuan (khung nhin 7 ngay Thu Hai -> Chu Nhat) -----


class DutyWeekPlanBrief(BaseModel):
    """Trang thai phe duyet bang truc tuan cua tung don vi (ma tran don doc)."""

    plan_id: int
    unit_id: int
    unit_name: str
    status: str
    status_label: str
    entry_count: int
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]


class DutyWeekDay(BaseModel):
    date: date
    weekday_label: str
    is_today: bool
    entries: list[DutyScheduleOut]
    entry_count: int
    personnel_present: int
    personnel_total: int


class DutyWeekBoard(BaseModel):
    week_start: date
    week_end: date
    week_label: str  # VD "Tuần 36/2026"
    days: list[DutyWeekDay]
    unit_plans: list[DutyWeekPlanBrief]
    total_entries: int
