from typing import Optional, Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.duty_plan_attachment import DutyPlanAttachment


def _q(db: Session):
    return db.query(DutyPlanAttachment).options(joinedload(DutyPlanAttachment.uploaded_by))


def create(
    db: Session,
    *,
    week_plan_id: int,
    file_url: str,
    original_name: str,
    file_size: int,
    content_type: Optional[str],
    label: Optional[str],
    uploaded_by_id: int,
) -> DutyPlanAttachment:
    row = DutyPlanAttachment(
        week_plan_id=week_plan_id,
        file_url=file_url,
        original_name=original_name,
        file_size=file_size,
        content_type=content_type,
        label=label,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get(db: Session, attachment_id: int) -> DutyPlanAttachment | None:
    return _q(db).filter(DutyPlanAttachment.id == attachment_id).first()


def list_for_plan(db: Session, week_plan_id: int) -> list[DutyPlanAttachment]:
    return (
        _q(db)
        .filter(DutyPlanAttachment.week_plan_id == week_plan_id)
        .order_by(DutyPlanAttachment.created_at.asc(), DutyPlanAttachment.id.asc())
        .all()
    )


def count_for_plans(db: Session, plan_ids: Sequence[int]) -> dict[int, int]:
    if not plan_ids:
        return {}
    rows = (
        db.query(DutyPlanAttachment.week_plan_id, func.count(DutyPlanAttachment.id))
        .filter(DutyPlanAttachment.week_plan_id.in_(list(plan_ids)))
        .group_by(DutyPlanAttachment.week_plan_id)
        .all()
    )
    return {pid: int(cnt) for pid, cnt in rows}


def delete(db: Session, row: DutyPlanAttachment) -> None:
    db.delete(row)
    db.commit()
