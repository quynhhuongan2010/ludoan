from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.duty import (
    APPROVED,
    DRAFT,
    PENDING,
    RETURNED,
    monday_of,
    sunday_of,
    week_label,
)
from app.core.roles import is_command
from app.core.uploads import delete_upload
from app.models.duty_week_plan import DutyWeekPlan
from app.models.user import User
from app.repositories import duty_schedule_repository, duty_week_plan_repository, unit_repository
from app.schemas.duty_schedule import (
    DutyScheduleCreate,
    DutyScheduleOut,
    duty_plan_status_label,
)
from app.schemas.duty_week_plan import (
    DutyWeekPlanCreate,
    DutyWeekPlanDetail,
    DutyWeekPlanOut,
    DutyWeekPlanReview,
    DutyWeekPlanUpdate,
)
from app.services.duty_schedule_service import _to_out as _entry_to_out

_EDITABLE_STATUSES = (DRAFT, RETURNED)


# ---------------------------------------------------------------- helpers ----


def _is_command_level(user: User) -> bool:
    return is_command(user)


def _name(user) -> Optional[str]:
    return user.full_name if user is not None else None


def _aggregates(plan: DutyWeekPlan) -> tuple[int, int, int]:
    entries = plan.entries
    present = sum(e.personnel_present or 0 for e in entries)
    total = sum(e.personnel_total or 0 for e in entries)
    return len(entries), present, total


def _to_out(plan: DutyWeekPlan) -> DutyWeekPlanOut:
    entry_count, present, total = _aggregates(plan)
    return DutyWeekPlanOut(
        id=plan.id,
        unit_id=plan.unit_id,
        unit_name=plan.unit.name if plan.unit is not None else "—",
        week_start=plan.week_start,
        week_end=sunday_of(plan.week_start),
        week_label=week_label(plan.week_start),
        status=plan.status,
        status_label=duty_plan_status_label(plan.status),
        note=plan.note,
        entry_count=entry_count,
        attachment_count=len(plan.attachments),
        personnel_present=present,
        personnel_total=total,
        submitted_by_id=plan.submitted_by_id,
        submitted_by_name=_name(plan.submitted_by),
        submitted_at=plan.submitted_at,
        reviewed_by_id=plan.reviewed_by_id,
        reviewed_by_name=_name(plan.reviewed_by),
        reviewed_at=plan.reviewed_at,
        review_note=plan.review_note,
        author_id=plan.author_id,
        author_full_name=plan.author.full_name if plan.author is not None else "—",
        created_at=plan.created_at,
    )


def _to_detail(plan: DutyWeekPlan) -> DutyWeekPlanDetail:
    # Import cuc bo: duty_plan_attachment_service import nguoc lai module nay.
    from app.services.duty_plan_attachment_service import _to_out as _attach_to_out

    base = _to_out(plan).model_dump()
    base["entries"] = [_entry_to_out(e) for e in plan.entries]
    base["attachments"] = [_attach_to_out(a) for a in plan.attachments]
    return DutyWeekPlanDetail(**base)


def _get_plan_or_404(db: Session, plan_id: int) -> DutyWeekPlan:
    plan = duty_week_plan_repository.get(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bảng trực tuần")
    return plan


def _require_owner_unit(plan: DutyWeekPlan, user: User) -> None:
    """officer chi thao tac bang cua chinh don vi minh; commander/admin: moi don vi."""
    if _is_command_level(user):
        return
    if plan.unit_id != user.unit_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không đủ quyền thực hiện thao tác này")


def _require_visible(plan: DutyWeekPlan, user: User) -> None:
    if _is_command_level(user) or plan.status == APPROVED or plan.unit_id == user.unit_id:
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bảng trực tuần")


# ------------------------------------------------------------------- CRUD ----


def create_plan(db: Session, plan_in: DutyWeekPlanCreate, current_user: User) -> DutyWeekPlanOut:
    if _is_command_level(current_user):
        unit_id = plan_in.unit_id
        if unit_repository.get(db, unit_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Đơn vị không tồn tại")
    else:
        if current_user.unit_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản chưa được gán đơn vị, không lập được bảng trực",
            )
        unit_id = current_user.unit_id  # ep ve don vi cua chinh minh

    monday = monday_of(plan_in.week_start)
    if duty_week_plan_repository.get_by_unit_week(db, unit_id, monday) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Đơn vị đã có bảng trực tuần cho tuần này",
        )

    plan = duty_week_plan_repository.create(
        db, unit_id=unit_id, week_start=monday, note=plan_in.note, author_id=current_user.id
    )
    return _to_out(duty_week_plan_repository.get(db, plan.id))


def list_plans(
    db: Session,
    current_user: User,
    *,
    unit_id: Optional[int] = None,
    week_of: Optional[date] = None,
    status_filter: Optional[str] = None,
) -> list[DutyWeekPlanOut]:
    week_start = monday_of(week_of) if week_of is not None else None
    statuses = [status_filter] if status_filter else None

    if _is_command_level(current_user):
        unit_ids = [unit_id] if unit_id is not None else None
        plans = duty_week_plan_repository.list_plans(
            db, unit_ids=unit_ids, week_start=week_start, statuses=statuses
        )
    else:
        # officer: bang cua don vi minh (moi trang thai) + bang da_duyet cua don vi khac
        own = duty_week_plan_repository.list_plans(
            db,
            unit_ids=[current_user.unit_id] if current_user.unit_id is not None else [-1],
            week_start=week_start,
            statuses=statuses,
        )
        approved = duty_week_plan_repository.list_plans(
            db, week_start=week_start, statuses=[APPROVED]
        )
        seen = {p.id for p in own}
        merged = own + [p for p in approved if p.id not in seen]
        if unit_id is not None:
            merged = [p for p in merged if p.unit_id == unit_id]
        if status_filter:
            merged = [p for p in merged if p.status == status_filter]
        plans = sorted(merged, key=lambda p: (p.week_start, p.unit_id, p.id), reverse=True)

    return [_to_out(p) for p in plans]


def get_plan_detail(db: Session, plan_id: int, current_user: User) -> DutyWeekPlanDetail:
    plan = _get_plan_or_404(db, plan_id)
    _require_visible(plan, current_user)
    return _to_detail(plan)


def update_plan(
    db: Session, plan_id: int, data: DutyWeekPlanUpdate, current_user: User
) -> DutyWeekPlanOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_owner_unit(plan, current_user)
    if plan.status not in _EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bảng trực tuần đã trình/duyệt, không sửa được",
        )
    duty_week_plan_repository.update_note(db, plan, data.note)
    return _to_out(duty_week_plan_repository.get(db, plan_id))


def delete_plan(db: Session, plan_id: int, current_user: User) -> None:
    plan = _get_plan_or_404(db, plan_id)
    _require_owner_unit(plan, current_user)
    if plan.status != DRAFT and not _is_command_level(current_user):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chỉ xoá được bảng trực tuần khi còn ở trạng thái nháp",
        )
    attachment_urls = [a.file_url for a in plan.attachments]
    duty_week_plan_repository.delete(db, plan)
    for url in attachment_urls:
        delete_upload(url)


# ------------------------------------------------------------- dong ca truc ----


def add_entry(
    db: Session, plan_id: int, entry_in: DutyScheduleCreate, current_user: User
) -> DutyScheduleOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_owner_unit(plan, current_user)
    if plan.status not in _EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bảng trực tuần đã trình/duyệt — mở lại (reopen) trước khi thêm dòng",
        )
    if not (plan.week_start <= entry_in.duty_date <= sunday_of(plan.week_start)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ngày trực nằm ngoài tuần của bảng trực",
        )
    entry = duty_schedule_repository.create(
        db,
        entry_in,
        week_plan_id=plan.id,
        unit_id=plan.unit_id,
        author_id=current_user.id,
    )
    return _entry_to_out(entry)


# ---------------------------------------------------------------- workflow ----


def submit_plan(db: Session, plan_id: int, current_user: User) -> DutyWeekPlanOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_owner_unit(plan, current_user)
    if plan.status not in (DRAFT, RETURNED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bảng trực tuần không ở trạng thái nháp/trả lại",
        )
    if not plan.entries:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bảng trực tuần chưa có dòng ca trực nào để trình",
        )
    duty_week_plan_repository.set_status(
        db,
        plan,
        PENDING,
        submitted_by_id=current_user.id,
        submitted_at=datetime.now(),
        clear_review=True,
    )
    return _to_out(duty_week_plan_repository.get(db, plan_id))


def review_plan(
    db: Session, plan_id: int, review_in: DutyWeekPlanReview, current_user: User
) -> DutyWeekPlanOut:
    plan = _get_plan_or_404(db, plan_id)
    if plan.status != PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bảng trực tuần không ở trạng thái chờ duyệt",
        )
    duty_week_plan_repository.set_status(
        db,
        plan,
        review_in.status,
        reviewed_by_id=current_user.id,
        reviewed_at=datetime.now(),
        review_note=review_in.review_note or "",
    )
    return _to_out(duty_week_plan_repository.get(db, plan_id))


def reopen_plan(db: Session, plan_id: int, current_user: User) -> DutyWeekPlanOut:
    """Mo lai bang ve nhap de dieu chinh.

    - `cho_duyet`  -> nhap : don vi so huu (rut lai) HOAC chi huy.
    - `da_duyet`   -> nhap : chi `commander`/`admin`.
    """
    plan = _get_plan_or_404(db, plan_id)
    if plan.status == PENDING:
        _require_owner_unit(plan, current_user)
    elif plan.status == APPROVED:
        if not _is_command_level(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ chỉ huy mới mở lại được bảng trực đã duyệt",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chỉ mở lại được bảng đang chờ duyệt hoặc đã duyệt",
        )
    duty_week_plan_repository.set_status(db, plan, DRAFT, clear_review=True)
    return _to_out(duty_week_plan_repository.get(db, plan_id))
