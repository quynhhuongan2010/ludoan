from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DutyShiftHandoverCreate(BaseModel):
    schedule_id: int = Field(..., description="ID dòng ca trực trong duty_schedules")
    giver_name: Optional[str] = Field(None, max_length=100, description="Tên người giao ca (mặc định lấy theo tài khoản)")
    receiver_id: Optional[int] = Field(None, description="ID tài khoản người nhận ca nếu có")
    receiver_name: Optional[str] = Field(None, max_length=100, description="Họ tên người nhận ca")
    personnel_report: Optional[str] = Field(None, description="Tình hình quân số: có mặt, vắng mặt có lý do...")
    equipment_status: Optional[str] = Field(None, description="Tình hình khí tài thông tin liên lạc, vũ khí trang bị")
    incident_log: Optional[str] = Field(None, description="Nhật ký các sự vụ, mệnh lệnh nhận được trong ca trực")
    pending_tasks: Optional[str] = Field(None, description="Nhiệm vụ còn dở dang bàn giao ca sau theo dõi, xử lý")


class DutyShiftHandoverAcknowledge(BaseModel):
    status: str = Field("da_nhan", pattern="^(da_nhan|co_kien_nghi)$", description="Trạng thái xác nhận: da_nhan hoặc co_kien_nghi")
    receiver_note: Optional[str] = Field(None, max_length=500, description="Ghi chú phản hồi hoặc kiến nghị của ca sau")


class DutyShiftHandoverCommanderReview(BaseModel):
    commander_note: str = Field(..., max_length=500, description="Ý kiến nhận xét, chỉ đạo của Chỉ huy ca trực")


class DutyShiftHandoverOut(BaseModel):
    id: int
    schedule_id: int
    duty_date: Optional[date] = None
    duty_type: Optional[str] = None
    shift: Optional[str] = None
    unit_name: Optional[str] = None
    giver_id: int
    giver_name: str
    receiver_id: Optional[int] = None
    receiver_name: Optional[str] = None
    handover_time: datetime
    personnel_report: Optional[str] = None
    equipment_status: Optional[str] = None
    incident_log: Optional[str] = None
    pending_tasks: Optional[str] = None
    commander_note: Optional[str] = None
    status: str
    receiver_note: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DutyShiftHandoverListResponse(BaseModel):
    items: list[DutyShiftHandoverOut]
    total: int
    skip: int
    limit: int
