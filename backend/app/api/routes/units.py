from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.roles import ADMIN_ROLES
from app.schemas.unit import UnitCreate, UnitKind, UnitOut
from app.services import unit_service

router = APIRouter(
    prefix="/units",
    tags=["units"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model=UnitOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)
def create_unit(unit_in: UnitCreate, db: Session = Depends(get_db)):
    return unit_service.create_unit(db, unit_in)


@router.get("/", response_model=list[UnitOut], status_code=status.HTTP_200_OK)
def list_units(
    skip: int = 0,
    limit: int = 200,
    kind: Optional[UnitKind] = None,
    active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return unit_service.list_units(db, skip=skip, limit=limit, kind=kind, active=active)


@router.get("/{unit_id}", response_model=UnitOut, status_code=status.HTTP_200_OK)
def get_unit(unit_id: int, db: Session = Depends(get_db)):
    return unit_service.get_unit(db, unit_id)


@router.put(
    "/{unit_id}",
    response_model=UnitOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)
def update_unit(unit_id: int, unit_in: UnitCreate, db: Session = Depends(get_db)):
    return unit_service.update_unit(db, unit_id, unit_in)


@router.delete(
    "/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)
def delete_unit(unit_id: int, db: Session = Depends(get_db)):
    unit_service.delete_unit(db, unit_id)
    return None
