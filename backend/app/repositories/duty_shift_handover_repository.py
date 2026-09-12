from datetime import date
from typing import Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models.duty_schedule import DutySchedule
from app.models.duty_shift_handover import DutyShiftHandover


def create(db: Session, handover: DutyShiftHandover) -> DutyShiftHandover:
    db.add(handover)
    db.commit()
    db.refresh(handover)
    return handover


def get_by_id(db: Session, handover_id: int) -> Optional[DutyShiftHandover]:
    return (
        db.query(DutyShiftHandover)
        .options(
            joinedload(DutyShiftHandover.schedule).joinedload(DutySchedule.unit),
            joinedload(DutyShiftHandover.giver),
            joinedload(DutyShiftHandover.receiver),
        )
        .filter(DutyShiftHandover.id == handover_id)
        .first()
    )


def get_by_schedule_id(db: Session, schedule_id: int) -> Optional[DutyShiftHandover]:
    return (
        db.query(DutyShiftHandover)
        .options(
            joinedload(DutyShiftHandover.schedule).joinedload(DutySchedule.unit),
            joinedload(DutyShiftHandover.giver),
            joinedload(DutyShiftHandover.receiver),
        )
        .filter(DutyShiftHandover.schedule_id == schedule_id)
        .order_by(desc(DutyShiftHandover.id))
        .first()
    )


def _filter_query(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    unit_id: Optional[int] = None,
    status: Optional[str] = None,
):
    q = (
        db.query(DutyShiftHandover)
        .join(DutySchedule, DutyShiftHandover.schedule_id == DutySchedule.id)
        .options(
            joinedload(DutyShiftHandover.schedule).joinedload(DutySchedule.unit),
            joinedload(DutyShiftHandover.giver),
            joinedload(DutyShiftHandover.receiver),
        )
    )
    if date_from:
        q = q.filter(DutySchedule.duty_date >= date_from)
    if date_to:
        q = q.filter(DutySchedule.duty_date <= date_to)
    if unit_id is not None:
        q = q.filter(DutySchedule.unit_id == unit_id)
    if status:
        q = q.filter(DutyShiftHandover.status == status)
    return q


def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    unit_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[DutyShiftHandover]:
    q = _filter_query(db, date_from=date_from, date_to=date_to, unit_id=unit_id, status=status)
    return (
        q.order_by(desc(DutyShiftHandover.handover_time), desc(DutyShiftHandover.id))
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_all(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    unit_id: Optional[int] = None,
    status: Optional[str] = None,
) -> int:
    q = _filter_query(db, date_from=date_from, date_to=date_to, unit_id=unit_id, status=status)
    return q.count()
