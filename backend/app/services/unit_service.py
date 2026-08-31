from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.unit import Unit
from app.repositories import unit_repository
from app.schemas.unit import UnitCreate, UnitOut


def _to_out(db: Session, unit: Unit) -> UnitOut:
    return UnitOut(
        id=unit.id,
        name=unit.name,
        unit_kind=unit.unit_kind,
        description=unit.description,
        is_active=unit.is_active,
        created_at=unit.created_at,
        user_count=unit_repository.count_users(db, unit.id),
    )


def create_unit(db: Session, unit_in: UnitCreate) -> UnitOut:
    if unit_repository.get_by_name(db, unit_in.name) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên đơn vị đã tồn tại")
    unit = unit_repository.create(db, unit_in)
    return _to_out(db, unit)


def list_units(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 200,
    kind: Optional[str] = None,
    active: Optional[bool] = None,
) -> list[UnitOut]:
    units = unit_repository.list_all(db, skip=skip, limit=limit, kind=kind, active=active)
    return [_to_out(db, u) for u in units]


def get_unit_or_404(db: Session, unit_id: int) -> Unit:
    unit = unit_repository.get(db, unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn vị không tồn tại")
    return unit


def get_unit(db: Session, unit_id: int) -> UnitOut:
    return _to_out(db, get_unit_or_404(db, unit_id))


def update_unit(db: Session, unit_id: int, unit_in: UnitCreate) -> UnitOut:
    unit = get_unit_or_404(db, unit_id)
    existing = unit_repository.get_by_name(db, unit_in.name)
    if existing is not None and existing.id != unit.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên đơn vị đã tồn tại")
    return _to_out(db, unit_repository.update(db, unit, unit_in))


def delete_unit(db: Session, unit_id: int) -> None:
    unit = get_unit_or_404(db, unit_id)
    if unit_repository.count_users(db, unit_id) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Không thể xoá: vẫn còn tài khoản thuộc đơn vị này",
        )
    unit_repository.delete(db, unit)
