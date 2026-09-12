from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.duty import (
    APPROVED,
    monday_of,
    sunday_of,
    week_days,
    week_label,
    weekday_label,
)
from app.core.roles import is_command
from app.models.duty_schedule import DutySchedule
from app.models.duty_week_plan import DutyWeekPlan
from app.models.user import User
from app.repositories import duty_schedule_repository, duty_week_plan_repository
from app.schemas.duty_schedule import (
    DutyDayBoard,
    DutyScheduleCreate,
    DutyScheduleOut,
    DutyUnitGroup,
    DutyWeekBoard,
    DutyWeekDay,
    DutyWeekPlanBrief,
    duty_plan_status_label,
    duty_type_label,
)

_NO_UNIT_LABEL = "Chưa gán đơn vị"
_EDITABLE_STATUSES = ("nhap", "tra_lai")


def _to_out(entry: DutySchedule) -> DutyScheduleOut:
    unit_name = entry.unit.name if entry.unit is not None else None
    return DutyScheduleOut(
        id=entry.id,
        week_plan_id=entry.week_plan_id,
        duty_date=entry.duty_date,
        unit_id=entry.unit_id,
        unit_name=unit_name,
        duty_type=entry.duty_type,
        duty_type_label=duty_type_label(entry.duty_type),
        shift=entry.shift,
        duty_officer=entry.duty_officer,
        role_title=entry.role_title,
        contact_phone=entry.contact_phone,
        personnel_present=entry.personnel_present,
        personnel_total=entry.personnel_total,
        note=entry.note,
        author_id=entry.author_id,
        author_full_name=entry.author.full_name,
        created_at=entry.created_at,
    )


def _is_command_level(user: User) -> bool:
    return is_command(user)


def _entry_visible(entry: DutySchedule, user: User) -> bool:
    """Ai duoc thay dong ca truc nay tren bang tong hop toan Lu doan."""
    if _is_command_level(user):
        return True
    plan = entry.week_plan
    if plan is None:  # ban ghi cu chua gan bang tuan -> chi don vi so huu thay
        return entry.unit_id is not None and entry.unit_id == user.unit_id
    if plan.status == APPROVED:
        return True
    return plan.unit_id == user.unit_id


def _plan_visible(plan: DutyWeekPlan, user: User) -> bool:
    if _is_command_level(user):
        return True
    if plan.status == APPROVED:
        return True
    return plan.unit_id == user.unit_id


# ----- Danh sach dong ca truc (dung cho tra cuu, loc) -----


def list_duties(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    unit_id: Optional[int] = None,
    duty_type: Optional[str] = None,
    *,
    current_user: User,
) -> list[DutyScheduleOut]:
    entries = duty_schedule_repository.list_all(
        db,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        unit_id=unit_id,
        duty_type=duty_type,
    )
    return [_to_out(e) for e in entries if _entry_visible(e, current_user)]


def get_duty_or_404(db: Session, entry_id: int, current_user: User) -> DutyScheduleOut:
    entry = duty_schedule_repository.get_with_author(db, entry_id)
    if entry is None or not _entry_visible(entry, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy dòng ca trực")
    return _to_out(entry)


# ----- Sua / xoa 1 dong ca truc (rang buoc theo trang thai bang cha) -----


def _get_editable_entry(db: Session, entry_id: int, current_user: User) -> DutySchedule:
    entry = duty_schedule_repository.get_with_author(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy dòng ca trực")
    plan = entry.week_plan
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dòng ca trực cũ chưa gắn bảng trực tuần, không sửa được",
        )
    if not _is_command_level(current_user) and plan.unit_id != current_user.unit_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không đủ quyền thực hiện thao tác này")
    if plan.status not in _EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bảng trực tuần đã trình/duyệt — mở lại (reopen) trước khi sửa",
        )
    return entry


def _check_entry_date(entry_in: DutyScheduleCreate, plan: DutyWeekPlan) -> None:
    if not (plan.week_start <= entry_in.duty_date <= sunday_of(plan.week_start)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ngày trực nằm ngoài tuần của bảng trực",
        )


def update_entry(
    db: Session, entry_id: int, entry_in: DutyScheduleCreate, current_user: User
) -> DutyScheduleOut:
    entry = _get_editable_entry(db, entry_id, current_user)
    _check_entry_date(entry_in, entry.week_plan)
    updated = duty_schedule_repository.update(db, entry, entry_in)
    return _to_out(updated)


def delete_entry(db: Session, entry_id: int, current_user: User) -> None:
    entry = _get_editable_entry(db, entry_id, current_user)
    duty_schedule_repository.delete(db, entry)


# ----- Tinh nang 1: bang kip truc toan Lu doan theo ngay, gom theo don vi -----


def build_day_board(
    db: Session, day: date, current_user: User, unit_id: Optional[int] = None
) -> DutyDayBoard:
    entries = duty_schedule_repository.list_for_range(db, day, day, unit_id=unit_id)
    visible = [e for e in entries if _entry_visible(e, current_user)]

    groups: dict[Optional[int], DutyUnitGroup] = {}
    for entry in visible:
        key = entry.unit_id
        group = groups.get(key)
        if group is None:
            plan = entry.week_plan
            group = DutyUnitGroup(
                unit_id=key,
                unit_name=entry.unit.name if entry.unit is not None else _NO_UNIT_LABEL,
                plan_id=plan.id if plan is not None else None,
                plan_status=plan.status if plan is not None else None,
                plan_status_label=(
                    duty_plan_status_label(plan.status) if plan is not None else None
                ),
                entries=[],
                entry_count=0,
                personnel_present=0,
                personnel_total=0,
            )
            groups[key] = group
        group.entries.append(_to_out(entry))
        group.entry_count += 1
        group.personnel_present += entry.personnel_present or 0
        group.personnel_total += entry.personnel_total or 0

    group_list = list(groups.values())
    return DutyDayBoard(
        date=day,
        weekday_label=weekday_label(day),
        groups=group_list,
        total_entries=sum(g.entry_count for g in group_list),
        personnel_present=sum(g.personnel_present for g in group_list),
        personnel_total=sum(g.personnel_total for g in group_list),
    )


# ----- Tinh nang 2: bang truc tuan (7 ngay Thu Hai -> Chu Nhat) -----


def build_week_board(
    db: Session, week_of: date, current_user: User, unit_id: Optional[int] = None
) -> DutyWeekBoard:
    monday = monday_of(week_of)
    sunday = sunday_of(monday)
    entries = duty_schedule_repository.list_for_range(db, monday, sunday, unit_id=unit_id)
    visible = [e for e in entries if _entry_visible(e, current_user)]

    today = date.today()
    days: list[DutyWeekDay] = []
    for current in week_days(monday):
        day_entries = [e for e in visible if e.duty_date == current]
        days.append(
            DutyWeekDay(
                date=current,
                weekday_label=weekday_label(current),
                is_today=current == today,
                entries=[_to_out(e) for e in day_entries],
                entry_count=len(day_entries),
                personnel_present=sum(e.personnel_present or 0 for e in day_entries),
                personnel_total=sum(e.personnel_total or 0 for e in day_entries),
            )
        )

    plans = duty_week_plan_repository.list_for_week(db, monday)
    if unit_id is not None:
        plans = [p for p in plans if p.unit_id == unit_id]
    unit_plans = [
        DutyWeekPlanBrief(
            plan_id=p.id,
            unit_id=p.unit_id,
            unit_name=p.unit.name if p.unit is not None else _NO_UNIT_LABEL,
            status=p.status,
            status_label=duty_plan_status_label(p.status),
            entry_count=len(p.entries),
            submitted_at=p.submitted_at,
            reviewed_at=p.reviewed_at,
        )
        for p in plans
        if _plan_visible(p, current_user)
    ]

    return DutyWeekBoard(
        week_start=monday,
        week_end=sunday,
        week_label=week_label(monday),
        days=days,
        unit_plans=unit_plans,
        total_entries=len(visible),
    )
