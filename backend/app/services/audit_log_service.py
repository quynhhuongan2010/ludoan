import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.roles import is_command
from app.models.user import User
from app.repositories import audit_log_repository as repo
from app.schemas.audit_log import AuditLogCreate, AuditLogListResponse, AuditLogOut

logger = logging.getLogger(__name__)


def record_action(
    db: Session,
    action: str,
    actor: Optional[User] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    target_name: Optional[str] = None,
    ip_address: Optional[str] = None,
    is_success: bool = True,
    details: Optional[str] = None,
) -> None:
    """Ghi nhat ky an ninh mang khong ngat quang nghiep vu chinh."""
    try:
        actor_id = actor.id if actor else None
        actor_username = actor.username if actor else None
        actor_full_name = actor.full_name if actor else None
        actor_role = actor.role if actor else None

        payload = AuditLogCreate(
            actor_id=actor_id,
            actor_username=actor_username,
            actor_full_name=actor_full_name,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            target_name=target_name,
            ip_address=ip_address,
            is_success=is_success,
            details=details,
        )
        repo.create(db, payload)
    except Exception as e:  # noqa: BLE001
        logger.exception("Khong the ghi audit log cho hanh dong %s: %s", action, e)


def get_audit_logs(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 50,
    action: Optional[str] = None,
    actor_id: Optional[int] = None,
    target_type: Optional[str] = None,
    is_success: Optional[bool] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> AuditLogListResponse:
    # Chi Ban Chi huy va Admin moi duoc xem So Nhat ky an ninh
    if not is_command(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Ban Chỉ huy và Quản trị hệ thống mới có quyền xem Nhật ký an ninh",
        )

    if page < 1:
        page = 1
    if page_size < 1 or page_size > 200:
        page_size = 50

    skip = (page - 1) * page_size
    items = repo.list_all(
        db,
        skip=skip,
        limit=page_size,
        action=action,
        actor_id=actor_id,
        target_type=target_type,
        is_success=is_success,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )
    total = repo.count_all(
        db,
        action=action,
        actor_id=actor_id,
        target_type=target_type,
        is_success=is_success,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )

    return AuditLogListResponse(
        items=[AuditLogOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
