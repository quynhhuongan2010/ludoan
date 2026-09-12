from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.leadership_task import (
    LeadershipTaskCreate,
    LeadershipTaskListResponse,
    LeadershipTaskOut,
    LeadershipTaskReport,
    LeadershipTaskReview,
)
from app.services import leadership_task_service

router = APIRouter(
    prefix="/leadership-tasks",
    tags=["leadership-tasks"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=LeadershipTaskListResponse, status_code=status.HTTP_200_OK)
def list_leadership_tasks(
    skip: int = 0,
    limit: int = 50,
    commander_role: Optional[str] = Query(
        None,
        description="Chức danh Ban Chỉ huy: lu_truong | chinh_uy | lu_pho_tmt | lu_pho_hckt | pho_chinh_uy",
    ),
    target_branch: Optional[str] = Query(
        None,
        description="Ngành công tác: tham_muu | chinh_tri | hau_can_ky_thuat",
    ),
    assigned_unit_id: Optional[int] = Query(None, description="Đơn vị được giao"),
    status: Optional[str] = Query(
        None,
        description="Trạng thái: dang_thuc_hien | da_bao_cao | da_hoan_thanh | can_bo_sung",
    ),
    urgency: Optional[str] = Query(
        None,
        description="Độ khẩn: thuong | khan | hoa_toc",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danh sách & Tra cứu các chỉ đạo, giao việc của Ban Chỉ huy Lữ đoàn.

    Ban Chỉ huy (role 0–3) thấy mọi chỉ đạo; tài khoản khác (role 4–5) chỉ thấy
    chỉ đạo giao cho đơn vị mình hoặc chỉ đạo phạm vi rộng thuộc khối/ngành mình.
    """
    return leadership_task_service.list_tasks(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        commander_role=commander_role,
        target_branch=target_branch,
        assigned_unit_id=assigned_unit_id,
        status=status,
        urgency=urgency,
    )


@router.get("/{id}", response_model=LeadershipTaskOut, status_code=status.HTTP_200_OK)
def get_leadership_task(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chi tiết một chỉ đạo tác chiến / nhiệm vụ giao của Chỉ huy Lữ đoàn.

    Ngoài phạm vi xem của tài khoản (không thuộc đơn vị/ngành được giao) → 404.
    """
    return leadership_task_service.get_task(db=db, current_user=current_user, task_id=id)


@router.post("", response_model=LeadershipTaskOut, status_code=status.HTTP_201_CREATED)
def create_leadership_task(
    payload: LeadershipTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ban Chỉ huy Lữ đoàn ban hành Chỉ đạo, Mệnh lệnh, Giao việc mới (Yêu cầu role <= 2)."""
    return leadership_task_service.create_task(
        db=db, current_user=current_user, payload=payload
    )


@router.post("/{id}/report", response_model=LeadershipTaskOut, status_code=status.HTTP_200_OK)
def report_leadership_task(
    id: int,
    payload: LeadershipTaskReport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Đơn vị cơ sở hoặc trợ lý ban ngành báo cáo tiến độ / kết quả thực hiện chỉ đạo."""
    return leadership_task_service.submit_report(
        db=db, current_user=current_user, task_id=id, payload=payload
    )


@router.post("/{id}/review", response_model=LeadershipTaskOut, status_code=status.HTTP_200_OK)
def review_leadership_task(
    id: int,
    payload: LeadershipTaskReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ban Chỉ huy Lữ đoàn đánh giá kết quả, bút phê chỉ đạo bổ sung hoặc kết luận hoàn thành."""
    return leadership_task_service.review_task(
        db=db, current_user=current_user, task_id=id, payload=payload
    )
