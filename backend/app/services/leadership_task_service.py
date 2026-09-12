"""Service xu ly nghiep vu cho Bàn làm việc & Chi dao cua Ban Chi huy Lu doan (v7.7.0)."""

from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.rbac import BRANCH_LABELS, can_manage_branch, get_user_branch
from app.core.roles import can_post_content, is_command
from app.models.leadership_task import LeadershipTask
from app.models.unit import Unit
from app.models.user import User
from app.repositories import leadership_task_repository as repo
from app.schemas.leadership_task import (
    COMMANDER_ROLE_LABELS,
    TASK_STATUS_LABELS,
    URGENCY_LABELS,
    LeadershipTaskCreate,
    LeadershipTaskListResponse,
    LeadershipTaskOut,
    LeadershipTaskReport,
    LeadershipTaskReview,
)
from app.services import audit_log_service


def _to_out(task: LeadershipTask) -> LeadershipTaskOut:
    unit_name = task.assigned_unit.name if task.assigned_unit else task.assigned_unit_name
    return LeadershipTaskOut(
        id=task.id,
        commander_role=task.commander_role,
        commander_role_label=COMMANDER_ROLE_LABELS.get(task.commander_role, task.commander_role),
        commander_id=task.commander_id,
        commander_name=task.commander_name,
        title=task.title,
        content=task.content,
        target_branch=task.target_branch,
        target_branch_label=BRANCH_LABELS.get(task.target_branch, task.target_branch),
        assigned_unit_id=task.assigned_unit_id,
        assigned_unit_name=unit_name,
        urgency=task.urgency,
        urgency_label=URGENCY_LABELS.get(task.urgency, task.urgency),
        deadline=task.deadline,
        status=task.status,
        status_label=TASK_STATUS_LABELS.get(task.status, task.status),
        report_content=task.report_content,
        reported_by_id=task.reported_by_id,
        reported_by_name=task.reported_by_name,
        reported_at=task.reported_at,
        review_note=task.review_note,
        reviewed_at=task.reviewed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def create_task(
    db: Session, current_user: User, payload: LeadershipTaskCreate
) -> LeadershipTaskOut:
    # 1. Chi cap Ban Chi huy Lu doan (role 0, 1, 2) moi duoc ban hanh y kien chi dao
    if current_user.role is None or current_user.role > 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ các đồng chí trong Ban Chỉ huy Lữ đoàn mới có thẩm quyền ban hành Mệnh lệnh / Chỉ đạo.",
        )

    assigned_unit_name = None
    if payload.assigned_unit_id:
        unit = db.query(Unit).filter(Unit.id == payload.assigned_unit_id).first()
        if unit:
            assigned_unit_name = unit.name

    commander_name = current_user.full_name or current_user.username
    task = LeadershipTask(
        commander_role=payload.commander_role,
        commander_id=current_user.id,
        commander_name=commander_name,
        title=payload.title,
        content=payload.content,
        target_branch=payload.target_branch,
        assigned_unit_id=payload.assigned_unit_id,
        assigned_unit_name=assigned_unit_name,
        urgency=payload.urgency,
        deadline=payload.deadline,
        status="dang_thuc_hien",
    )

    created = repo.create(db, task)

    # Ghi log an ninh
    audit_log_service.record_action(
        db,
        action="LEADERSHIP_TASK_CREATED",
        actor=current_user,
        target_type="leadership_task",
        target_id=str(created.id),
        target_name=created.title,
        details=f"Chỉ huy {commander_name} ({payload.commander_role}) ban hành chỉ đạo: {created.title}",
    )

    return _to_out(created)


def _can_report_on_task(user: User, task: LeadershipTask) -> bool:
    """Ai duoc nop bao cao ket qua cho mot chi dao cua BCH Lu doan.

    - Ban Chi huy Lu doan (role 0..3): luon duoc (theo doi / bao cao thay).
    - Tai khoan `role >= 5` (chi xem): khong duoc.
    - Neu chi dao giao cho MOT don vi cu the: chi can bo dung don vi do.
    - Neu khong giao don vi cu the: chi dao pham vi `toan_lu_doan` -> moi can bo
      deu bao cao duoc; chi dao theo khoi/nganh -> can bo dung khoi/nganh do.
    """
    if is_command(user):
        return True
    if not can_post_content(user):  # role 5 (Nguoi dung) khong nop bao cao chinh thuc
        return False
    if task.assigned_unit_id is not None:
        return user.unit_id == task.assigned_unit_id
    if not task.target_branch or task.target_branch == "toan_lu_doan":
        return True
    return can_manage_branch(user, task.target_branch)


def _viewer_scope(user: User) -> tuple[bool, Optional[int], list[str]]:
    """Pham vi xem danh sach chi dao cho tai khoan KHONG thuoc Ban Chi huy.

    Tra ve `(restrict, viewer_unit_id, viewer_branches)`:
      - restrict=False  -> Ban Chi huy (role 0..3): xem moi chi dao.
      - restrict=True   -> chi thay chi dao giao cho don vi minh + chi dao pham vi
                           rong thuoc khoi/nganh minh phu trach.
    """
    if is_command(user):
        return False, None, []
    branch = get_user_branch(user)
    branches = [branch] if branch and branch != "don_vi_co_so" else []
    return True, user.unit_id, branches


def _can_view_task(user: User, task: LeadershipTask) -> bool:
    """Tai khoan `user` co duoc xem chi tiet mot chi dao cu the khong."""
    if is_command(user):
        return True
    if task.assigned_unit_id is not None:
        return user.unit_id is not None and user.unit_id == task.assigned_unit_id
    if not task.target_branch or task.target_branch == "toan_lu_doan":
        return True
    return can_manage_branch(user, task.target_branch)


def submit_report(
    db: Session, current_user: User, task_id: int, payload: LeadershipTaskReport
) -> LeadershipTaskOut:
    task = repo.get_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy chỉ đạo của Ban Chỉ huy Lữ đoàn",
        )

    if not _can_report_on_task(current_user, task):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Đồng chí không thuộc đơn vị / ngành được giao chỉ đạo này nên không thể nộp báo cáo kết quả.",
        )

    reporter_name = current_user.full_name or current_user.username
    task.report_content = payload.report_content
    task.reported_by_id = current_user.id
    task.reported_by_name = reporter_name
    task.reported_at = datetime.now()
    # Nop bao cao -> chuyen sang "da_bao_cao" cho BCH but phe (tru khi da ket luan
    # hoan thanh thi giu nguyen).
    if task.status != "da_hoan_thanh":
        task.status = "da_bao_cao"

    updated = repo.update(db, task)

    # Ghi log an ninh
    audit_log_service.record_action(
        db,
        action="LEADERSHIP_TASK_REPORTED",
        actor=current_user,
        target_type="leadership_task",
        target_id=str(task.id),
        target_name=task.title,
        details=f"Đồng chí {reporter_name} báo cáo kết quả thực hiện chỉ đạo: {task.title}",
    )

    return _to_out(updated)


def review_task(
    db: Session, current_user: User, task_id: int, payload: LeadershipTaskReview
) -> LeadershipTaskOut:
    if current_user.role is None or current_user.role > 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ các đồng chí trong Ban Chỉ huy Lữ đoàn mới có thẩm quyền phê duyệt báo cáo nhiệm vụ.",
        )

    task = repo.get_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy chỉ đạo của Ban Chỉ huy Lữ đoàn",
        )

    task.status = payload.status
    task.review_note = payload.review_note
    task.reviewed_at = datetime.now()

    updated = repo.update(db, task)

    # Ghi log an ninh
    audit_log_service.record_action(
        db,
        action="LEADERSHIP_TASK_REVIEWED",
        actor=current_user,
        target_type="leadership_task",
        target_id=str(task.id),
        target_name=task.title,
        details=f"Chỉ huy {current_user.full_name or current_user.username} phê duyệt chỉ đạo {task.title} (kết quả: {payload.status})",
    )

    return _to_out(updated)


def get_task(db: Session, current_user: User, task_id: int) -> LeadershipTaskOut:
    task = repo.get_by_id(db, task_id)
    if not task or not _can_view_task(current_user, task):
        # Khong lo tinh ton tai cua chi dao voi tai khoan ngoai pham vi -> 404.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy chỉ đạo của Ban Chỉ huy Lữ đoàn",
        )
    return _to_out(task)


def list_tasks(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    commander_role: Optional[str] = None,
    target_branch: Optional[str] = None,
    assigned_unit_id: Optional[int] = None,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
) -> LeadershipTaskListResponse:
    restrict, viewer_unit_id, viewer_branches = _viewer_scope(current_user)
    items = repo.list_all(
        db=db,
        skip=skip,
        limit=limit,
        commander_role=commander_role,
        target_branch=target_branch,
        assigned_unit_id=assigned_unit_id,
        status=status,
        urgency=urgency,
        restrict_to_viewer=restrict,
        viewer_unit_id=viewer_unit_id,
        viewer_branches=viewer_branches,
    )
    total = repo.count_all(
        db=db,
        commander_role=commander_role,
        target_branch=target_branch,
        assigned_unit_id=assigned_unit_id,
        status=status,
        urgency=urgency,
        restrict_to_viewer=restrict,
        viewer_unit_id=viewer_unit_id,
        viewer_branches=viewer_branches,
    )
    return LeadershipTaskListResponse(items=[_to_out(t) for t in items], total=total)
