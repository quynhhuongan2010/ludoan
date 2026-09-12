from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.roles import CONTENT_ROLES
from app.models.user import User
from app.schemas.duty_schedule import (
    DutyDayBoard,
    DutyScheduleCreate,
    DutyScheduleOut,
    DutyWeekBoard,
)
from app.services import duty_schedule_service

router = APIRouter(
    prefix="/duty-schedules",
    tags=["duty-schedules"],
    dependencies=[Depends(get_current_user)],
)

# Ghi chu: tao dong ca truc di qua bang cha -> POST /duty-week-plans/{id}/entries.
# Router nay chi con doc (danh sach + bang tong hop) va sua/xoa tung dong.


@router.get("", response_model=list[DutyScheduleOut], status_code=status.HTTP_200_OK)
def list_duties(
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    unit_id: Optional[int] = None,
    duty_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_schedule_service.list_duties(
        db, skip, limit, date_from, date_to, unit_id, duty_type, current_user=current_user
    )


@router.get("/board/day", response_model=DutyDayBoard, status_code=status.HTTP_200_OK)
def duty_day_board(
    day: date = Query(..., description="Ngày cần xem kíp trực toàn Lữ đoàn"),
    unit_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tính năng 1: kíp trực toàn Lữ đoàn theo ngày, gom theo đơn vị + tổng quân số.

    Chỉ huy Lữ đoàn thấy mọi trạng thái bảng trực tuần (kèm nhãn); đơn vị cấp
    dưới chỉ thấy bảng đã duyệt của đơn vị khác và mọi trạng thái của đơn vị mình.
    """
    return duty_schedule_service.build_day_board(db, day, current_user, unit_id)


@router.get("/board/week", response_model=DutyWeekBoard, status_code=status.HTTP_200_OK)
def duty_week_board(
    week_of: date = Query(..., description="Ngày bất kỳ trong tuần cần xem (chuẩn hoá về Thứ Hai)"),
    unit_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tính năng 2: trực tuần - khung nhìn 7 ngày (Thứ Hai → Chủ Nhật) + ma trận
    trạng thái phê duyệt bảng trực tuần của từng đơn vị."""
    return duty_schedule_service.build_week_board(db, week_of, current_user, unit_id)


@router.get("/{entry_id}", response_model=DutyScheduleOut, status_code=status.HTTP_200_OK)
def get_duty(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_schedule_service.get_duty_or_404(db, entry_id, current_user)


@router.put(
    "/{entry_id}",
    response_model=DutyScheduleOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def update_duty(
    entry_id: int,
    entry_in: DutyScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return duty_schedule_service.update_entry(db, entry_id, entry_in, current_user)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*CONTENT_ROLES))],
)
def delete_duty(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    duty_schedule_service.delete_entry(db, entry_id, current_user)
    return None
