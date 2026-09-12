from datetime import datetime
from typing import Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate


def create(db: Session, payload: AuditLogCreate) -> AuditLog:
    log = AuditLog(
        actor_id=payload.actor_id,
        actor_username=payload.actor_username,
        actor_full_name=payload.actor_full_name,
        actor_role=payload.actor_role,
        action=payload.action,
        target_type=payload.target_type,
        target_id=payload.target_id,
        target_name=payload.target_name,
        ip_address=payload.ip_address,
        is_success=payload.is_success,
        details=payload.details,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _filter_query(
    db: Session,
    action: Optional[str] = None,
    actor_id: Optional[int] = None,
    target_type: Optional[str] = None,
    is_success: Optional[bool] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
):
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if actor_id is not None:
        q = q.filter(AuditLog.actor_id == actor_id)
    if target_type:
        q = q.filter(AuditLog.target_type == target_type)
    if is_success is not None:
        q = q.filter(AuditLog.is_success.is_(is_success))
    if from_date:
        q = q.filter(AuditLog.created_at >= from_date)
    if to_date:
        q = q.filter(AuditLog.created_at <= to_date)
    if search:
        s = f"%{search.strip()}%"
        q = q.filter(
            (AuditLog.actor_full_name.ilike(s))
            | (AuditLog.actor_username.ilike(s))
            | (AuditLog.target_name.ilike(s))
            | (AuditLog.details.ilike(s))
            | (AuditLog.ip_address.ilike(s))
        )
    return q


def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    actor_id: Optional[int] = None,
    target_type: Optional[str] = None,
    is_success: Optional[bool] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> list[AuditLog]:
    q = _filter_query(
        db,
        action=action,
        actor_id=actor_id,
        target_type=target_type,
        is_success=is_success,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )
    return q.order_by(desc(AuditLog.created_at), desc(AuditLog.id)).offset(skip).limit(limit).all()


def count_all(
    db: Session,
    action: Optional[str] = None,
    actor_id: Optional[int] = None,
    target_type: Optional[str] = None,
    is_success: Optional[bool] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> int:
    q = _filter_query(
        db,
        action=action,
        actor_id=actor_id,
        target_type=target_type,
        is_success=is_success,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )
    return q.count()
