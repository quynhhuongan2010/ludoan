from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DispatchDirection = Literal["di", "den"]
DispatchStatus = Literal["moi", "dang_xu_ly", "da_xu_ly", "luu_tru"]

# Loai van ban (van thu nghiep vu). Khop frontend/src/types/commandDispatch.ts.
DocType = Literal[
    "cong_van",
    "dien_mat",
    "chi_thi",
    "quyet_dinh",
    "menh_lenh",
    "thong_bao",
    "thong_tri",
    "ke_hoach",
    "bao_cao",
    "to_trinh",
    "bien_ban",
    "huong_dan",
    "giay_moi",
    "khac",
]

# Do mat
SecurityLevel = Literal["thuong", "mat", "toi_mat", "tuyet_mat"]
# Do khan
Urgency = Literal["thuong", "khan", "thuong_khan", "hoa_toc"]


class DispatchUpdate(BaseModel):
    direction: DispatchDirection
    doc_type: DocType = "cong_van"
    dispatch_number: str = Field(..., min_length=1, max_length=80)
    summary: str = Field(..., min_length=1, max_length=500)
    issuing_org: Optional[str] = Field(default=None, max_length=200)
    receiving_org: Optional[str] = Field(default=None, max_length=200)
    signer: Optional[str] = Field(default=None, max_length=200)
    issued_date: Optional[date] = None
    received_date: Optional[date] = None
    deadline: Optional[date] = None
    page_count: Optional[int] = Field(default=None, ge=0, le=100000)
    security_level: SecurityLevel = "mat"
    urgency: Urgency = "thuong"
    archive_ref: Optional[str] = Field(default=None, max_length=120)
    status: DispatchStatus = "moi"
    note: Optional[str] = None


class AcknowledgeRequest(BaseModel):
    response_note: Optional[str] = Field(default=None, max_length=500)


class DispatchAckOut(BaseModel):
    user_id: int
    full_name: str
    role: int
    acknowledged_at: Optional[datetime] = None
    response_note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OfficialDispatchOut(BaseModel):
    id: int
    direction: DispatchDirection
    doc_type: str
    dispatch_number: str
    summary: str
    issuing_org: Optional[str]
    receiving_org: Optional[str]
    signer: Optional[str]
    issued_date: Optional[date]
    received_date: Optional[date]
    deadline: Optional[date]
    page_count: Optional[int]
    security_level: str
    urgency: str
    archive_ref: Optional[str]
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
