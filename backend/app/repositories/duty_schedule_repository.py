from datetime import date
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.duty_schedule import DutySchedule
from app.models.duty_week_plan import DutyWeekPlan
from app.schemas.duty_schedule import DutyScheduleCreate

_ORDER = (DutySchedule.duty_date.desc(), DutySchedule.id.desc())
# Thu tu doc bang ngay/tuan: tang dan theo ngay, gom theo don vi roi cuong vi.
_BOARD_ORDER = (
    DutySchedule.duty_date.asc(),
    DutySchedule.unit_id.asc(),
    DutySchedule.duty_type.asc(),
    DutySchedule.id.asc(),
)


def _base_query(db: Session):
    return db.query(DutySchedule).options(
        joinedload(DutySchedule.author),
        joinedload(DutySchedule.unit),
        joinedload(DutySchedule.week_plan).joinedload(DutyWeekPlan.unit),
    )


def create(
    db: Session,
    entry_in: DutyScheduleCreate,
    *,
    week_plan_id: int,
    unit_id: Optional[int],
    author_id: int,
) -> DutySchedule:
    entry = DutySchedule(
        **entry_in.model_dump(),
        week_plan_id=week_plan_id,
        unit_id=unit_id,
        author_id=author_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_all(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    unit_id: Optional[int] = None,
    duty_type: Optional[str] = None,
) -> list[DutySchedule]:
    query = _base_query(db)
    if date_from is not None:
        query = query.filter(DutySchedule.duty_date >= date_from)
    if date_to is not None:
        query = query.filter(DutySchedule.duty_date <= date_to)
    if unit_id is not None:
        query = query.filter(DutySchedule.unit_id == unit_id)
    if duty_type is not None:
        query = query.filter(DutySchedule.duty_type == duty_type)
    return query.order_by(*_ORDER).offset(skip).limit(limit).all()


def list_for_range(
    db: Session,
    date_from: date,
    date_to: date,
    *,
    unit_id: Optional[int] = None,
) -> list[DutySchedule]:
    """Toan bo ca truc trong [date_from, date_to] kem bang cha - phuc vu bang tong hop."""
    query = _base_query(db).filter(
        DutySchedule.duty_date >= date_from,
        DutySchedule.duty_date <= date_to,
    )
    if unit_id is not None:
        query = query.filter(DutySchedule.unit_id == unit_id)
    return query.order_by(*_BOARD_ORDER).all()


def get_with_author(db: Session, entry_id: int) -> DutySchedule | None:
    return _base_query(db).filter(DutySchedule.id == entry_id).first()


def get(db: Session, entry_id: int) -> DutySchedule | None:
    return db.get(DutySchedule, entry_id)


def update(db: Session, entry: DutySchedule, entry_in: DutyScheduleCreate) -> DutySchedule:
    for field, value in entry_in.model_dump().items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete(db: Session, entry: DutySchedule) -> None:
    db.delete(entry)
    db.commit()
