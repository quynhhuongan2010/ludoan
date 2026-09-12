from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogCreate(BaseModel):
    actor_id: Optional[int] = None
    actor_username: Optional[str] = None
    actor_full_name: Optional[str] = None
    actor_role: Optional[int] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    ip_address: Optional[str] = None
    is_success: bool = True
    details: Optional[str] = None


class AuditLogOut(BaseModel):
    id: int
    created_at: datetime
    actor_id: Optional[int] = None
    actor_username: Optional[str] = None
    actor_full_name: Optional[str] = None
    actor_role: Optional[int] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    ip_address: Optional[str] = None
    is_success: bool
    details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int
