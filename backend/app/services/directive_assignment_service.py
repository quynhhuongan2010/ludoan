from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.access import can_access_directive_channel, is_command_level
from app.core.uploads import SavedFile
from app.models.directive import Directive
from app.models.directive_assignment import (
    DirectiveAssignment,
    DirectiveAssignmentTarget,
    DirectiveSubmission,
)
from app.models.user import User
from app.repositories import directive_assignment_repository as repo
from app.repositories import unit_repository
from app.schemas.directive_assignment import (
    DirectiveAssignmentCreate,
    DirectiveAssignmentDetailOut,
    DirectiveAssignmentOut,
    DirectiveAssignmentUpdate,
    ReviewRequest,
    SubmissionOut,
    TargetCreate,
    TargetDetailOut,
)

_NOT_FOUND = "Không tìm thấy nhiệm vụ"
_TARGET_NOT_FOUND = "Không tìm thấy đối tượng được giao"
_APPROVED = "da_duyet"
_PENDING_REVIEW = "cho_duyet"


# --------------------------------------------------------------------------- guards
def _require_channel(user: User) -> None:
    if not can_access_directive_channel(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập Kênh Chỉ đạo – Báo cáo",
        )


def _require_commander(user: User) -> None:
    if not is_command_level(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Ban chỉ huy được thao tác giao nhiệm vụ / duyệt báo cáo",
        )


def _target_belongs_to_user(target: DirectiveAssignmentTarget, user: User) -> bool:
    if target.assignee_id is not None:
        return target.assignee_id == user.id
    return user.unit_id is not None and target.unit_id == user.unit_id


def _check_directive(db: Session, directive_id: Optional[int]) -> None:
    if directive_id is not None and db.get(Directive, directive_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chỉ thị không tồn tại")


def _check_units(db: Session, unit_ids: list[int]) -> None:
    for uid in set(unit_ids):
        if unit_repository.get(db, uid) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Đơn vị #{uid} không tồn tại"
            )


# --------------------------------------------------------------------------- status
def _recompute_status(db: Session, assignment: DirectiveAssignment) -> None:
    targets = assignment.targets
    if not targets:
        new = "chua_giao"
    elif all(t.status == _APPROVED for t in targets):
        new = "hoan_thanh"
    else:
        new = "dang_thuc_hien"
    repo.set_assignment_status(db, assignment, new)


def _effective_status(a: DirectiveAssignment) -> str:
    if (
        a.status not in ("hoan_thanh", "chua_giao")
        and a.due_date is not None
        and a.due_date < date.today()
    ):
        return "qua_han"
    return a.status


# --------------------------------------------------------------------------- mappers
def _submission_out(s: DirectiveSubmission) -> SubmissionOut:
    return SubmissionOut(
        id=s.id,
        target_id=s.target_id,
        content=s.content,
        attachment_url=s.attachment_url,
        submitted_by_id=s.submitted_by_id,
        submitted_by_full_name=s.submitted_by.full_name if s.submitted_by else "",
        created_at=s.created_at,
        review_result=s.review_result,
        review_note=s.review_note,
        reviewed_by_id=s.reviewed_by_id,
        reviewed_at=s.reviewed_at,
    )


def _target_detail_out(t: DirectiveAssignmentTarget) -> TargetDetailOut:
    return TargetDetailOut(
        id=t.id,
        assignment_id=t.assignment_id,
        unit_id=t.unit_id,
        unit_name=t.unit.name if t.unit else f"#{t.unit_id}",
        assignee_id=t.assignee_id,
        assignee_full_name=t.assignee.full_name if t.assignee else None,
        status=t.status,
        submitted_at=t.submitted_at,
        submission_count=len(t.submissions),
        submissions=[_submission_out(s) for s in t.submissions],
    )


def _assignment_out(
    a: DirectiveAssignment, current_user: User, *, detail: bool
) -> DirectiveAssignmentOut:
    see_all = is_command_level(current_user)
    targets = list(a.targets)
    if not see_all:
        targets = [t for t in targets if _target_belongs_to_user(t, current_user)]

    approved = sum(1 for t in targets if t.status == _APPROVED)
    base = dict(
        id=a.id,
        directive_id=a.directive_id,
        directive_title=a.directive.title if a.directive else None,
        title=a.title,
        description=a.description,
        due_date=a.due_date,
        status=_effective_status(a),
        created_by_id=a.created_by_id,
        created_by_full_name=a.created_by.full_name if a.created_by else "",
        created_at=a.created_at,
        target_count=len(targets),
        approved_count=approved,
        pending_count=len(targets) - approved,
    )
    if not detail:
        return DirectiveAssignmentOut(**base)
    return DirectiveAssignmentDetailOut(
        **base, targets=[_target_detail_out(t) for t in targets]
    )


# --------------------------------------------------------------------------- queries
def _get_or_404(db: Session, assignment_id: int) -> DirectiveAssignment:
    a = repo.get_assignment(db, assignment_id)
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return a


def _visible_or_404(db: Session, assignment_id: int, user: User) -> DirectiveAssignment:
    a = _get_or_404(db, assignment_id)
    if not is_command_level(user) and not any(
        _target_belongs_to_user(t, user) for t in a.targets
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return a


def _get_target_or_404(
    db: Session, assignment_id: int, target_id: int
) -> DirectiveAssignmentTarget:
    t = repo.get_target(db, target_id)
    if t is None or t.assignment_id != assignment_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_TARGET_NOT_FOUND)
    return t


# --------------------------------------------------------------------------- use-cases
def create_assignment(
    db: Session, user: User, payload: DirectiveAssignmentCreate
) -> DirectiveAssignmentDetailOut:
    _require_commander(user)
    _check_directive(db, payload.directive_id)
    _check_units(db, [t.unit_id for t in payload.targets])

    a = repo.create_assignment(
        db,
        directive_id=payload.directive_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        created_by_id=user.id,
    )
    if payload.targets:
        repo.add_targets(db, a.id, [(t.unit_id, t.assignee_id) for t in payload.targets])
    a = repo.get_assignment(db, a.id)
    _recompute_status(db, a)
    return _assignment_out(a, user, detail=True)


def list_assignments(
    db: Session,
    user: User,
    *,
    status_filter: Optional[str] = None,
    directive_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[DirectiveAssignmentOut]:
    _require_channel(user)
    see_all = is_command_level(user)
    rows = repo.list_assignments(
        db,
        see_all=see_all,
        unit_id=None if see_all else user.unit_id,
        assignee_id=None if see_all else user.id,
        status=status_filter,
        directive_id=directive_id,
        skip=skip,
        limit=limit,
    )
    return [_assignment_out(a, user, detail=False) for a in rows]


def get_assignment(
    db: Session, user: User, assignment_id: int
) -> DirectiveAssignmentDetailOut:
    _require_channel(user)
    a = _visible_or_404(db, assignment_id, user)
    return _assignment_out(a, user, detail=True)


def update_assignment(
    db: Session, user: User, assignment_id: int, payload: DirectiveAssignmentUpdate
) -> DirectiveAssignmentDetailOut:
    _require_commander(user)
    a = _get_or_404(db, assignment_id)
    _check_directive(db, payload.directive_id)
    repo.update_assignment(
        db,
        a,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        directive_id=payload.directive_id,
    )
    a = repo.get_assignment(db, assignment_id)
    return _assignment_out(a, user, detail=True)


def delete_assignment(db: Session, user: User, assignment_id: int) -> None:
    _require_commander(user)
    a = _get_or_404(db, assignment_id)
    repo.delete_assignment(db, a)


def add_targets(
    db: Session, user: User, assignment_id: int, targets: list[TargetCreate]
) -> DirectiveAssignmentDetailOut:
    _require_commander(user)
    a = _get_or_404(db, assignment_id)
    _check_units(db, [t.unit_id for t in targets])
    existing = {(t.unit_id, t.assignee_id) for t in a.targets}
    for t in targets:
        if (t.unit_id, t.assignee_id) in existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Đối tượng này đã được giao trong nhiệm vụ",
            )
    repo.add_targets(db, assignment_id, [(t.unit_id, t.assignee_id) for t in targets])
    a = repo.get_assignment(db, assignment_id)
    _recompute_status(db, a)
    return _assignment_out(a, user, detail=True)


def remove_target(
    db: Session, user: User, assignment_id: int, target_id: int
) -> DirectiveAssignmentDetailOut:
    _require_commander(user)
    _get_or_404(db, assignment_id)
    t = _get_target_or_404(db, assignment_id, target_id)
    repo.delete_target(db, t)
    a = repo.get_assignment(db, assignment_id)
    _recompute_status(db, a)
    return _assignment_out(a, user, detail=True)


def submit_report(
    db: Session,
    user: User,
    assignment_id: int,
    target_id: int,
    content: str,
    saved: Optional[SavedFile],
) -> TargetDetailOut:
    _require_channel(user)
    _visible_or_404(db, assignment_id, user)
    t = _get_target_or_404(db, assignment_id, target_id)
    if not _target_belongs_to_user(t, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nhiệm vụ này không giao cho bạn / đơn vị bạn",
        )
    if t.status == _APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Nhiệm vụ đã được duyệt, không thể nộp lại"
        )
    content = (content or "").strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nội dung báo cáo không được để trống"
        )
    repo.add_submission(
        db,
        target_id=target_id,
        content=content,
        attachment_url=saved.url if saved else None,
        submitted_by_id=user.id,
    )
    t.status = _PENDING_REVIEW
    t.submitted_at = func.now()
    repo.save(db, t)
    a = repo.get_assignment(db, assignment_id)
    _recompute_status(db, a)
    return _target_detail_out(repo.get_target(db, target_id))


def review_target(
    db: Session,
    user: User,
    assignment_id: int,
    target_id: int,
    payload: ReviewRequest,
) -> TargetDetailOut:
    _require_commander(user)
    _get_or_404(db, assignment_id)
    t = _get_target_or_404(db, assignment_id, target_id)
    if t.status != _PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chỉ duyệt được đối tượng đang ở trạng thái 'chờ duyệt'",
        )
    latest = repo.latest_submission(db, target_id)
    if latest is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Chưa có báo cáo nào để duyệt"
        )
    latest.review_result = payload.result
    latest.review_note = payload.review_note
    latest.reviewed_by_id = user.id
    latest.reviewed_at = func.now()
    t.status = payload.result
    repo.save(db, latest)
    repo.save(db, t)
    a = repo.get_assignment(db, assignment_id)
    _recompute_status(db, a)
    return _target_detail_out(repo.get_target(db, target_id))
