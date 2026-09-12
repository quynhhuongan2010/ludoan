from datetime import date, datetime
from typing import Optional, Sequence

from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.duty_plan_attachment import DutyPlanAttachment
from app.models.duty_schedule import DutySchedule
from app.models.duty_week_plan import DutyWeekPlan

_ORDER = (DutyWeekPlan.week_start.desc(), DutyWeekPlan.unit_id.asc(), DutyWeekPlan.id.desc())


def _base_query(db: Session):
    return db.query(DutyWeekPlan).options(
        joinedload(DutyWeekPlan.unit),
        joinedload(DutyWeekPlan.author),
        joinedload(DutyWeekPlan.submitted_by),
        joinedload(DutyWeekPlan.reviewed_by),
        selectinload(DutyWeekPlan.attachments).joinedload(DutyPlanAttachment.uploaded_by),
    )


def _detail_query(db: Session):
    return _base_query(db).options(
        joinedload(DutyWeekPlan.entries).joinedload(DutySchedule.author),
        joinedload(DutyWeekPlan.entries).joinedload(DutySchedule.unit),
    )


def create(
    db: Session,
    *,
    unit_id: int,
    week_start: date,
    note: Optional[str],
    author_id: int,
) -> DutyWeekPlan:
    plan = DutyWeekPlan(
        unit_id=unit_id,
        week_start=week_start,
        note=note,
        author_id=author_id,
        status="nhap",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get(db: Session, plan_id: int) -> DutyWeekPlan | None:
    return _detail_query(db).filter(DutyWeekPlan.id == plan_id).first()


def get_by_unit_week(db: Session, unit_id: int, week_start: date) -> DutyWeekPlan | None:
    return (
        db.query(DutyWeekPlan)
        .filter(DutyWeekPlan.unit_id == unit_id, DutyWeekPlan.week_start == week_start)
        .first()
    )


def list_plans(
    db: Session,
    *,
    unit_ids: Optional[Sequence[int]] = None,
    week_start: Optional[date] = None,
    statuses: Optional[Sequence[str]] = None,
    skip: int = 0,
    limit: int = 200,
) -> list[DutyWeekPlan]:
    query = _base_query(db)
    if unit_ids is not None:
        query = query.filter(DutyWeekPlan.unit_id.in_(unit_ids))
    if week_start is not None:
        query = query.filter(DutyWeekPlan.week_start == week_start)
    if statuses is not None:
        query = query.filter(DutyWeekPlan.status.in_(statuses))
    return query.order_by(*_ORDER).offset(skip).limit(limit).all()


def list_for_week(db: Session, week_start: date) -> list[DutyWeekPlan]:
    return _base_query(db).filter(DutyWeekPlan.week_start == week_start).order_by(
        DutyWeekPlan.unit_id.asc()
    ).all()


def update_note(db: Session, plan: DutyWeekPlan, note: Optional[str]) -> DutyWeekPlan:
    plan.note = note
    db.commit()
    db.refresh(plan)
    return plan


def set_status(
    db: Session,
    plan: DutyWeekPlan,
    status: str,
    *,
    submitted_by_id: Optional[int] = None,
    submitted_at: Optional[datetime] = None,
    reviewed_by_id: Optional[int] = None,
    reviewed_at: Optional[datetime] = None,
    review_note: Optional[str] = None,
    clear_submit: bool = False,
    clear_review: bool = False,
) -> DutyWeekPlan:
    plan.status = status
    if submitted_by_id is not None:
        plan.submitted_by_id = submitted_by_id
    if submitted_at is not None:
        plan.submitted_at = submitted_at
    if clear_submit:
        plan.submitted_by_id = None
        plan.submitted_at = None
    if reviewed_by_id is not None:
        plan.reviewed_by_id = reviewed_by_id
    if reviewed_at is not None:
        plan.reviewed_at = reviewed_at
    if review_note is not None:
        plan.review_note = review_note
    if clear_review:
        plan.reviewed_by_id = None
        plan.reviewed_at = None
        plan.review_note = None
    db.commit()
    db.refresh(plan)
    return plan


def delete(db: Session, plan: DutyWeekPlan) -> None:
    db.delete(plan)
    db.commit()
