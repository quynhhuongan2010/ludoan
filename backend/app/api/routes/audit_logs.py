from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.audit_log import AuditLogListResponse
from app.services import audit_log_service as service

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=AuditLogListResponse, status_code=status.HTTP_200_OK)
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    actor_id: Optional[int] = Query(None),
    target_type: Optional[str] = Query(None),
    is_success: Optional[bool] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_audit_logs(
        db,
        current_user,
        page=page,
        page_size=page_size,
        action=action,
        actor_id=actor_id,
        target_type=target_type,
        is_success=is_success,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )
