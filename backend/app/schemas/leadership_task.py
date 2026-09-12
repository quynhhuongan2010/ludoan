"""Pydantic Schemas cho Nhiem vu & Y kien chi dao cua Ban Chi huy Lu doan (v7.7.0)."""

from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

CommanderRole = Literal["lu_truong", "chinh_uy", "lu_pho_tmt", "lu_pho_hckt", "pho_chinh_uy"]
TargetBranch = Literal["tham_muu", "chinh_tri", "hau_can_ky_thuat", "toan_lu_doan"]
Urgency = Literal["hoa_toc", "khan", "thuong"]
# Vong doi trang thai: dang_thuc_hien -> (submit_report) da_bao_cao
#   -> (review_task) da_hoan_thanh | can_bo_sung ; can_bo_sung + submit_report -> da_bao_cao
TaskStatus = Literal["dang_thuc_hien", "da_bao_cao", "da_hoan_thanh", "can_bo_sung"]
ReviewStatus = Literal["da_hoan_thanh", "can_bo_sung"]

COMMANDER_ROLE_LABELS = {
    "lu_truong": "Lữ đoàn trưởng (Chỉ đạo chung mọi mặt về Chính quyền)",
    "chinh_uy": "Chính uỷ Lữ đoàn (Chỉ đạo chung mọi mặt bên Đảng)",
    "lu_pho_tmt": "Phó Lữ đoàn trưởng kiêm TMT (Chỉ đạo chuyên ngành Tham mưu - Tác chiến - TTLL)",
    "lu_pho_hckt": "Phó Lữ đoàn trưởng HC-KT (Chỉ đạo chuyên ngành Hậu cần - Kỹ thuật - VKTB)",
    "pho_chinh_uy": "Phó Chính uỷ Lữ đoàn (Điều hành các Tổ chức Quần chúng & Tổ chức Đảng)",
}

URGENCY_LABELS = {
    "hoa_toc": "Hoả tốc",
    "khan": "Khẩn",
    "thuong": "Thường",
}

TASK_STATUS_LABELS = {
    "dang_thuc_hien": "Đang thực hiện",
    "da_bao_cao": "Đã báo cáo, chờ bút phê",
    "da_hoan_thanh": "Đã hoàn thành",
    "can_bo_sung": "Cần báo cáo bổ sung",
}


class LeadershipTaskCreate(BaseModel):
    commander_role: CommanderRole = Field(..., description="lu_truong | chinh_uy | lu_pho_tmt | lu_pho_hckt | pho_chinh_uy")
    title: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=5)
    target_branch: TargetBranch = Field("toan_lu_doan", description="tham_muu | chinh_tri | hau_can_ky_thuat | toan_lu_doan")
    assigned_unit_id: Optional[int] = None
    urgency: Urgency = Field("thuong", description="hoa_toc | khan | thuong")
    deadline: Optional[date] = None


class LeadershipTaskReport(BaseModel):
    report_content: str = Field(..., min_length=5, description="Báo cáo tiến độ và kết quả thực hiện chỉ đạo")


class LeadershipTaskReview(BaseModel):
    status: ReviewStatus = Field("da_hoan_thanh", description="Kết luận bút phê: da_hoan_thanh | can_bo_sung")
    review_note: str = Field(..., min_length=2, description="Ý kiến đánh giá, nhận xét của Chỉ huy Lữ đoàn")


class LeadershipTaskOut(BaseModel):
    id: int
    commander_role: str
    commander_role_label: str
    commander_id: int
    commander_name: str
    title: str
    content: str
    target_branch: str
    target_branch_label: str
    assigned_unit_id: Optional[int] = None
    assigned_unit_name: Optional[str] = None
    urgency: str
    urgency_label: str
    deadline: Optional[date] = None
    status: str
    status_label: str
    report_content: Optional[str] = None
    reported_by_id: Optional[int] = None
    reported_by_name: Optional[str] = None
    reported_at: Optional[datetime] = None
    review_note: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadershipTaskListResponse(BaseModel):
    items: list[LeadershipTaskOut]
    total: int
