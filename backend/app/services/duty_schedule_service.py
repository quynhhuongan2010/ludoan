from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.duty_schedule import DutySchedule
from app.models.user import User
from app.repositories import duty_schedule_repository
from app.schemas.duty_schedule import DutyScheduleCreate, DutyScheduleOut


def _to_out(duty: DutySchedule) -> DutyScheduleOut:
    return DutyScheduleOut(
        id=duty.id,
        duty_date=duty.duty_date,
        shift=duty.shift,
        duty_officer=duty.duty_officer,
        role_title=duty.role_title,
        note=duty.note,
        author_id=duty.author_id,
        author_full_name=duty.author.full_name,
        created_at=duty.created_at,
    )


def create_duty(db: Session, duty_in: DutyScheduleCreate, current_user: User) -> DutyScheduleOut:
    duty = duty_schedule_repository.create(db, duty_in, author_id=current_user.id)
    return _to_out(duty)


def list_duties(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[DutyScheduleOut]:
    duties = duty_schedule_repository.list_all(
        db, skip=skip, limit=limit, date_from=date_from, date_to=date_to
    )
    return [_to_out(d) for d in duties]


def get_duty_or_404(db: Session, duty_id: int) -> DutyScheduleOut:
    duty = duty_schedule_repository.get_with_author(db, duty_id)
    if duty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty schedule not found")
    return _to_out(duty)


def _get_owned_or_404(db: Session, duty_id: int, current_user: User) -> DutySchedule:
    duty = duty_schedule_repository.get_with_author(db, duty_id)
    if duty is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Duty schedule not found")
    if current_user.role != "commander" and duty.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return duty


def update_duty(
    db: Session, duty_id: int, duty_in: DutyScheduleCreate, current_user: User
) -> DutyScheduleOut:
    duty = _get_owned_or_404(db, duty_id, current_user)
    updated = duty_schedule_repository.update(db, duty, duty_in)
    return _to_out(updated)


def delete_duty(db: Session, duty_id: int, current_user: User) -> None:
    duty = _get_owned_or_404(db, duty_id, current_user)
    duty_schedule_repository.delete(db, duty)
