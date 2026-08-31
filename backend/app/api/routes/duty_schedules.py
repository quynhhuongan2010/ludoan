from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.duty_schedule import DutyScheduleCreate, DutyScheduleOut
from app.services import duty_schedule_service

router = APIRouter(
    prefix="/duty-schedules",
    tags=["duty-schedules"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=DutyScheduleOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def create_duty(
    duty_in: DutyScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_schedule_service.create_duty(db, duty_in, current_user)


@router.get("", response_model=list[DutyScheduleOut], status_code=status.HTTP_200_OK)
def list_duties(
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    return duty_schedule_service.list_duties(db, skip, limit, date_from, date_to)


@router.get("/{duty_id}", response_model=DutyScheduleOut, status_code=status.HTTP_200_OK)
def get_duty(duty_id: int, db: Session = Depends(get_db)):
    return duty_schedule_service.get_duty_or_404(db, duty_id)


@router.put(
    "/{duty_id}",
    response_model=DutyScheduleOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def update_duty(
    duty_id: int,
    duty_in: DutyScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_schedule_service.update_duty(db, duty_id, duty_in, current_user)


@router.delete(
    "/{duty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def delete_duty(
    duty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    duty_schedule_service.delete_duty(db, duty_id, current_user)
    return None
