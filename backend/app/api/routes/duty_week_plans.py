from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.roles import COMMAND_ROLES, CONTENT_ROLES
from app.models.user import User
from app.schemas.duty_plan_attachment import MAX_LABEL_LEN, DutyPlanAttachmentOut
from app.schemas.duty_schedule import DutyScheduleCreate, DutyScheduleOut
from app.schemas.duty_week_plan import (
    DutyWeekPlanCreate,
    DutyWeekPlanDetail,
    DutyWeekPlanOut,
    DutyWeekPlanReview,
    DutyWeekPlanUpdate,
)
from app.services import duty_plan_attachment_service, duty_week_plan_service

router = APIRouter(
    prefix="/duty-week-plans",
    tags=["duty-week-plans"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=DutyWeekPlanOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def create_plan(
    plan_in: DutyWeekPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_week_plan_service.create_plan(db, plan_in, current_user)


@router.get("", response_model=list[DutyWeekPlanOut], status_code=status.HTTP_200_OK)
def list_plans(
    unit_id: Optional[int] = None,
    week_of: Optional[date] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_week_plan_service.list_plans(
        db, current_user, unit_id=unit_id, week_of=week_of, status_filter=status_filter
    )


@router.get("/{plan_id}", response_model=DutyWeekPlanDetail, status_code=status.HTTP_200_OK)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_week_plan_service.get_plan_detail(db, plan_id, current_user)


@router.put(
    "/{plan_id}",
    response_model=DutyWeekPlanOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def update_plan(
    plan_id: int,
    data: DutyWeekPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_week_plan_service.update_plan(db, plan_id, data, current_user)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    duty_week_plan_service.delete_plan(db, plan_id, current_user)
    return None


@router.post(
    "/{plan_id}/entries",
    response_model=DutyScheduleOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def add_entry(
    plan_id: int,
    entry_in: DutyScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_week_plan_service.add_entry(db, plan_id, entry_in, current_user)


@router.get(
    "/{plan_id}/attachments",
    response_model=list[DutyPlanAttachmentOut],
    status_code=status.HTTP_200_OK,
)
def list_plan_attachments(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_plan_attachment_service.list_attachments(db, plan_id, current_user)


@router.post(
    "/{plan_id}/attachments",
    response_model=DutyPlanAttachmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def add_plan_attachment(
    plan_id: int,
    file: UploadFile = File(..., description="Tệp lịch trực: .pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx/.jpg/.jpeg/.png/.webp/.gif"),
    label: Optional[str] = Form(None, max_length=MAX_LABEL_LEN, description="Mô tả ngắn (không bắt buộc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_plan_attachment_service.add_attachment(db, plan_id, file, label, current_user)


@router.delete(
    "/{plan_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def delete_plan_attachment(
    plan_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    duty_plan_attachment_service.delete_attachment(db, plan_id, attachment_id, current_user)
    return None


@router.post(
    "/{plan_id}/submit",
    response_model=DutyWeekPlanOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def submit_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_week_plan_service.submit_plan(db, plan_id, current_user)


@router.post(
    "/{plan_id}/review",
    response_model=DutyWeekPlanOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def review_plan(
    plan_id: int,
    review_in: DutyWeekPlanReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_week_plan_service.review_plan(db, plan_id, review_in, current_user)


@router.post(
    "/{plan_id}/reopen",
    response_model=DutyWeekPlanOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def reopen_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_week_plan_service.reopen_plan(db, plan_id, current_user)
