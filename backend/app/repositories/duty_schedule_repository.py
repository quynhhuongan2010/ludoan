from datetime import date
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.duty_schedule import DutySchedule
from app.schemas.duty_schedule import DutyScheduleCreate

_ORDER = (DutySchedule.duty_date.desc(), DutySchedule.id.desc())


def create(db: Session, duty_in: DutyScheduleCreate, author_id: int) -> DutySchedule:
    duty = DutySchedule(**duty_in.model_dump(), author_id=author_id)
    db.add(duty)
    db.commit()
    db.refresh(duty)
    return duty


def list_all(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[DutySchedule]:
    query = db.query(DutySchedule).options(joinedload(DutySchedule.author))
    if date_from is not None:
        query = query.filter(DutySchedule.duty_date >= date_from)
    if date_to is not None:
        query = query.filter(DutySchedule.duty_date <= date_to)
    return query.order_by(*_ORDER).offset(skip).limit(limit).all()


def get_with_author(db: Session, duty_id: int) -> DutySchedule | None:
    return (
        db.query(DutySchedule)
        .options(joinedload(DutySchedule.author))
        .filter(DutySchedule.id == duty_id)
        .first()
    )


def get(db: Session, duty_id: int) -> DutySchedule | None:
    return db.get(DutySchedule, duty_id)


def update(db: Session, duty: DutySchedule, duty_in: DutyScheduleCreate) -> DutySchedule:
    for field, value in duty_in.model_dump().items():
        setattr(duty, field, value)
    db.commit()
    db.refresh(duty)
    return duty


def delete(db: Session, duty: DutySchedule) -> None:
    db.delete(duty)
    db.commit()
