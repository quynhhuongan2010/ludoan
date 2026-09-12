"""Repository cho Nhiem vu & Y kien chi dao cua Ban Chi huy Lu doan (v7.7.0)."""

from typing import Optional, Sequence
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Query, Session, joinedload

from app.models.leadership_task import LeadershipTask

# Pham vi "rong" luon hien voi moi tai khoan da kich hoat (khong gan don vi cu the).
_WIDE_BRANCHES = ("", "toan_lu_doan")


def create(db: Session, task: LeadershipTask) -> LeadershipTask:
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_by_id(db: Session, task_id: int) -> Optional[LeadershipTask]:
    return (
        db.query(LeadershipTask)
        .options(
            joinedload(LeadershipTask.commander),
            joinedload(LeadershipTask.assigned_unit),
            joinedload(LeadershipTask.reported_by),
        )
        .filter(LeadershipTask.id == task_id)
        .first()
    )


def _apply_filters(
    q: Query,
    *,
    commander_role: Optional[str],
    target_branch: Optional[str],
    assigned_unit_id: Optional[int],
    status: Optional[str],
    urgency: Optional[str],
    restrict_to_viewer: bool = False,
    viewer_unit_id: Optional[int] = None,
    viewer_branches: Sequence[str] = (),
) -> Query:
    if commander_role:
        q = q.filter(LeadershipTask.commander_role == commander_role)
    if target_branch:
        q = q.filter(LeadershipTask.target_branch == target_branch)
    if assigned_unit_id:
        q = q.filter(LeadershipTask.assigned_unit_id == assigned_unit_id)
    if status:
        q = q.filter(LeadershipTask.status == status)
    if urgency:
        q = q.filter(LeadershipTask.urgency == urgency)

    # Tai khoan KHONG thuoc Ban Chi huy (role 4-5): chi thay chi dao giao cho
    # dung don vi minh, hoac chi dao pham vi rong (khong gan don vi) thuoc khoi
    # nganh minh phu trach / pham vi toan Lu doan.
    if restrict_to_viewer:
        allowed_wide = [*_WIDE_BRANCHES, *viewer_branches]
        wide = and_(
            LeadershipTask.assigned_unit_id.is_(None),
            or_(
                LeadershipTask.target_branch.is_(None),
                LeadershipTask.target_branch.in_(allowed_wide),
            ),
        )
        if viewer_unit_id is not None:
            q = q.filter(or_(LeadershipTask.assigned_unit_id == viewer_unit_id, wide))
        else:
            q = q.filter(wide)
    return q


def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    commander_role: Optional[str] = None,
    target_branch: Optional[str] = None,
    assigned_unit_id: Optional[int] = None,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    *,
    restrict_to_viewer: bool = False,
    viewer_unit_id: Optional[int] = None,
    viewer_branches: Sequence[str] = (),
) -> list[LeadershipTask]:
    q = db.query(LeadershipTask).options(
        joinedload(LeadershipTask.commander),
        joinedload(LeadershipTask.assigned_unit),
        joinedload(LeadershipTask.reported_by),
    )
    q = _apply_filters(
        q,
        commander_role=commander_role,
        target_branch=target_branch,
        assigned_unit_id=assigned_unit_id,
        status=status,
        urgency=urgency,
        restrict_to_viewer=restrict_to_viewer,
        viewer_unit_id=viewer_unit_id,
        viewer_branches=viewer_branches,
    )
    return q.order_by(desc(LeadershipTask.created_at)).offset(skip).limit(limit).all()


def count_all(
    db: Session,
    commander_role: Optional[str] = None,
    target_branch: Optional[str] = None,
    assigned_unit_id: Optional[int] = None,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    *,
    restrict_to_viewer: bool = False,
    viewer_unit_id: Optional[int] = None,
    viewer_branches: Sequence[str] = (),
) -> int:
    q = _apply_filters(
        db.query(LeadershipTask),
        commander_role=commander_role,
        target_branch=target_branch,
        assigned_unit_id=assigned_unit_id,
        status=status,
        urgency=urgency,
        restrict_to_viewer=restrict_to_viewer,
        viewer_unit_id=viewer_unit_id,
        viewer_branches=viewer_branches,
    )
    return q.count()


def update(db: Session, task: LeadershipTask) -> LeadershipTask:
    db.commit()
    db.refresh(task)
    return task
