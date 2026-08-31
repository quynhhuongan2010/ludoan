from typing import Optional

from sqlalchemy.orm import Session

from app.models.unit import Unit
from app.models.user import User
from app.schemas.unit import UnitCreate


def create(db: Session, unit_in: UnitCreate) -> Unit:
    unit = Unit(**unit_in.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def list_all(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 200,
    kind: Optional[str] = None,
    active: Optional[bool] = None,
) -> list[Unit]:
    query = db.query(Unit)
    if kind is not None:
        query = query.filter(Unit.unit_kind == kind)
    if active is not None:
        query = query.filter(Unit.is_active.is_(active))
    return query.order_by(Unit.unit_kind.asc(), Unit.name.asc()).offset(skip).limit(limit).all()


def get(db: Session, unit_id: int) -> Unit | None:
    return db.get(Unit, unit_id)


def get_by_name(db: Session, name: str) -> Unit | None:
    return db.query(Unit).filter(Unit.name == name).first()


def update(db: Session, unit: Unit, unit_in: UnitCreate) -> Unit:
    for field, value in unit_in.model_dump().items():
        setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return unit


def delete(db: Session, unit: Unit) -> None:
    db.delete(unit)
    db.commit()


def count_users(db: Session, unit_id: int) -> int:
    return db.query(User).filter(User.unit_id == unit_id).count()
