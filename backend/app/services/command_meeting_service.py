from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import can_access_command_channel, is_command_level
from app.core.config import settings
from app.core.uploads import SavedFile, delete_upload
from app.models.command_meeting import CommandMeeting, CommandMeetingAttendee
from app.models.user import User
from app.repositories import command_meeting_repository as repo
from app.repositories import user_repository
from app.schemas.command_meeting import (
    AttendanceUpdate,
    AttendeeOut,
    CommandMeetingCreate,
    CommandMeetingDetailOut,
    CommandMeetingOut,
    CommandMeetingUpdate,
)

_NOT_FOUND = "Không tìm thấy cuộc họp"
_ATT_NOT_FOUND = "Người này không có trong thành phần triệu tập"
_FORBIDDEN = "Bạn không có quyền truy cập Kênh chuyên BCH & Cấp uỷ (yêu cầu quyền MẬT)"


def _require_channel(user: User) -> None:
    if not can_access_command_channel(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_FORBIDDEN)


def _require_commander(user: User) -> None:
    if not is_command_level(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Ban chỉ huy được tạo / điều hành cuộc họp",
        )


def _validate_times(start: datetime, end: Optional[datetime]) -> None:
    if end is not None and end < start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thời gian kết thúc phải sau thời gian bắt đầu",
        )


def _resolve_users(db: Session, user_ids: list[int]) -> list[User]:
    users: list[User] = []
    for uid in dict.fromkeys(user_ids):
        u = user_repository.get_by_id(db, uid)
        if u is None or not u.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tài khoản #{uid} không tồn tại hoặc đã bị khoá",
            )
        users.append(u)
    return users


def _attendee_out(a: CommandMeetingAttendee) -> AttendeeOut:
    return AttendeeOut(
        id=a.id,
        meeting_id=a.meeting_id,
        user_id=a.user_id,
        full_name=a.user.full_name if a.user else "",
        unit_id=a.unit_id,
        unit_name=a.unit.name if a.unit else None,
        attendance=a.attendance,
        absence_reason=a.absence_reason,
        contribution_note=a.contribution_note,
    )


def _meeting_out(
    m: CommandMeeting, current_user: User, *, detail: bool
) -> CommandMeetingOut:
    mine = next((a for a in m.attendees if a.user_id == current_user.id), None)
    base = dict(
        id=m.id,
        title=m.title,
        start_time=m.start_time,
        end_time=m.end_time,
        location=m.location,
        meeting_link=m.meeting_link,
        agenda=m.agenda,
        minutes=m.minutes,
        attachment_url=m.attachment_url,
        attachment_name=m.attachment_name,
        status=m.status,
        classification=m.classification,
        created_by_id=m.created_by_id,
        created_by_full_name=m.created_by.full_name if m.created_by else "",
        created_at=m.created_at,
        attendee_count=len(m.attendees),
        present_count=sum(1 for a in m.attendees if a.attendance == "co_mat"),
        my_attendance=mine.attendance if mine else None,
    )
    if not detail:
        return CommandMeetingOut(**base)
    return CommandMeetingDetailOut(
        **base, attendees=[_attendee_out(a) for a in m.attendees]
    )


def _get_or_404(db: Session, meeting_id: int) -> CommandMeeting:
    m = repo.get(db, meeting_id)
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return m


# --------------------------------------------------------------------- use-cases
def create_meeting(
    db: Session, user: User, payload: CommandMeetingCreate
) -> CommandMeetingDetailOut:
    _require_commander(user)
    _validate_times(payload.start_time, payload.end_time)
    invitees = _resolve_users(db, payload.attendee_user_ids)
    m = repo.create(
        db,
        title=payload.title,
        start_time=payload.start_time,
        end_time=payload.end_time,
        location=payload.location,
        meeting_link=payload.meeting_link,
        agenda=payload.agenda,
        created_by_id=user.id,
    )
    if invitees:
        repo.add_attendees(db, m.id, [(u.id, u.unit_id) for u in invitees])
    return _meeting_out(repo.get(db, m.id), user, detail=True)


def list_meetings(
    db: Session,
    user: User,
    *,
    status_filter: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[CommandMeetingOut]:
    _require_channel(user)
    rows = repo.list_all(
        db,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return [_meeting_out(m, user, detail=False) for m in rows]


def get_meeting(db: Session, user: User, meeting_id: int) -> CommandMeetingDetailOut:
    _require_channel(user)
    return _meeting_out(_get_or_404(db, meeting_id), user, detail=True)


def update_meeting(
    db: Session, user: User, meeting_id: int, payload: CommandMeetingUpdate
) -> CommandMeetingDetailOut:
    _require_commander(user)
    m = _get_or_404(db, meeting_id)
    _validate_times(payload.start_time, payload.end_time)
    m.title = payload.title
    m.start_time = payload.start_time
    m.end_time = payload.end_time
    m.location = payload.location
    m.meeting_link = payload.meeting_link
    m.agenda = payload.agenda
    m.status = payload.status
    repo.save(db, m)
    return _meeting_out(repo.get(db, meeting_id), user, detail=True)


def delete_meeting(db: Session, user: User, meeting_id: int) -> None:
    _require_commander(user)
    m = _get_or_404(db, meeting_id)
    attachment = m.attachment_url
    repo.delete(db, m)
    delete_upload(attachment)


def set_minutes(
    db: Session, user: User, meeting_id: int, minutes: str, mark_finished: bool
) -> CommandMeetingDetailOut:
    _require_commander(user)
    m = _get_or_404(db, meeting_id)
    m.minutes = minutes
    if mark_finished:
        m.status = "da_ket_thuc"
    repo.save(db, m)
    return _meeting_out(repo.get(db, meeting_id), user, detail=True)


def set_attachment(
    db: Session, user: User, meeting_id: int, saved: SavedFile
) -> CommandMeetingDetailOut:
    _require_commander(user)
    m = _get_or_404(db, meeting_id)
    old = m.attachment_url
    m.attachment_url = saved.url
    m.attachment_name = saved.original_name
    m.content_type = saved.content_type
    repo.save(db, m)
    delete_upload(old)
    return _meeting_out(repo.get(db, meeting_id), user, detail=True)


def get_download_target(
    db: Session, user: User, meeting_id: int
) -> tuple[Path, str, str]:
    _require_channel(user)
    m = _get_or_404(db, meeting_id)
    if not m.attachment_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cuộc họp không có tài liệu đính kèm"
        )
    rel = (
        m.attachment_url[len("/static/") :]
        if m.attachment_url.startswith("/static/")
        else m.attachment_url
    )
    path = (settings.upload_path / rel).resolve()
    if settings.upload_path.resolve() not in path.parents or not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File không tồn tại trên máy chủ"
        )
    return path, m.attachment_name or path.name, m.content_type or "application/octet-stream"


def invite(
    db: Session, user: User, meeting_id: int, user_ids: list[int]
) -> CommandMeetingDetailOut:
    _require_commander(user)
    m = _get_or_404(db, meeting_id)
    invitees = _resolve_users(db, user_ids)
    existing = {a.user_id for a in m.attendees}
    for u in invitees:
        if u.id in existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{u.full_name} đã có trong thành phần triệu tập",
            )
    repo.add_attendees(db, meeting_id, [(u.id, u.unit_id) for u in invitees])
    return _meeting_out(repo.get(db, meeting_id), user, detail=True)


def remove_attendee(db: Session, user: User, meeting_id: int, target_user_id: int) -> None:
    _require_commander(user)
    _get_or_404(db, meeting_id)
    a = repo.get_attendee(db, meeting_id, target_user_id)
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ATT_NOT_FOUND)
    repo.delete_attendee(db, a)


def update_attendance(
    db: Session,
    current_user: User,
    meeting_id: int,
    target_user_id: int,
    payload: AttendanceUpdate,
) -> AttendeeOut:
    _require_channel(current_user)
    _get_or_404(db, meeting_id)
    if not is_command_level(current_user) and target_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn chỉ được cập nhật điểm danh / ý kiến của chính mình",
        )
    a = repo.get_attendee(db, meeting_id, target_user_id)
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ATT_NOT_FOUND)
    if payload.attendance is not None:
        a.attendance = payload.attendance
    if payload.absence_reason is not None:
        a.absence_reason = payload.absence_reason
    if payload.contribution_note is not None:
        a.contribution_note = payload.contribution_note
    repo.save(db, a)
    return _attendee_out(repo.get_attendee(db, meeting_id, target_user_id))
