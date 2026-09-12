from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.duty_shift_handover import (
    DutyShiftHandoverAcknowledge,
    DutyShiftHandoverCommanderReview,
    DutyShiftHandoverCreate,
    DutyShiftHandoverListResponse,
    DutyShiftHandoverOut,
)
from app.services import duty_shift_handover_service

router = APIRouter(
    prefix="/duty-shift-handovers",
    tags=["duty-shift-handovers"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=DutyShiftHandoverListResponse, status_code=status.HTTP_200_OK)
def list_shift_handovers(
    skip: int = 0,
    limit: int = 50,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    unit_id: Optional[int] = None,
    status: Optional[str] = Query(None, description="Trạng thái: cho_nhan | da_nhan | co_kien_nghi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tra cứu Sổ bàn giao ca trực & Nhật ký kíp trực toàn Lữ đoàn."""
    return duty_shift_handover_service.list_handovers(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        unit_id=unit_id,
        status=status,
    )


@router.get(
    "/by-schedule/{schedule_id}",
    response_model=Optional[DutyShiftHandoverOut],
    status_code=status.HTTP_200_OK,
)
def get_handover_by_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy chi tiết biên bản bàn giao gắn với một dòng ca trực cụ thể."""
    return duty_shift_handover_service.get_by_schedule(db=db, schedule_id=schedule_id)


@router.post("", response_model=DutyShiftHandoverOut, status_code=status.HTTP_201_CREATED)
def create_shift_handover(
    payload: DutyShiftHandoverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ca trước lập biên bản bàn giao ca trực điện tử."""
    return duty_shift_handover_service.create_handover(
        db=db, current_user=current_user, payload=payload
    )


@router.post(
    "/{id}/acknowledge",
    response_model=DutyShiftHandoverOut,
    status_code=status.HTTP_200_OK,
)
def acknowledge_shift_handover(
    id: int,
    payload: DutyShiftHandoverAcknowledge,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ca sau đối soát thực tế và ký nhận bàn giao ca trực."""
    return duty_shift_handover_service.acknowledge_handover(
        db=db, current_user=current_user, handover_id=id, payload=payload
    )


@router.post(
    "/{id}/review",
    response_model=DutyShiftHandoverOut,
    status_code=status.HTTP_200_OK,
)
def review_shift_handover(
    id: int,
    payload: DutyShiftHandoverCommanderReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cấp Chỉ huy kiểm tra và ghi ý kiến chỉ đạo vào sổ ca trực."""
    return duty_shift_handover_service.review_handover(
        db=db, current_user=current_user, handover_id=id, payload=payload
    )
