from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.command_meeting import CommandMeeting, CommandMeetingAttendee

_LOADS = (
    joinedload(CommandMeeting.created_by),
    joinedload(CommandMeeting.attendees).joinedload(CommandMeetingAttendee.user),
    joinedload(CommandMeeting.attendees).joinedload(CommandMeetingAttendee.unit),
)


def create(db: Session, **fields) -> CommandMeeting:
    obj = CommandMeeting(**fields)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def save(db: Session, obj) -> None:
    db.add(obj)
    db.commit()
    db.refresh(obj)


def get(db: Session, meeting_id: int) -> CommandMeeting | None:
    return (
        db.query(CommandMeeting)
        .options(*_LOADS)
        .filter(CommandMeeting.id == meeting_id)
        .first()
    )


def list_all(
    db: Session,
    *,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[CommandMeeting]:
    query = db.query(CommandMeeting).options(*_LOADS)
    if status is not None:
        query = query.filter(CommandMeeting.status == status)
    if date_from is not None:
        query = query.filter(CommandMeeting.start_time >= date_from)
    if date_to is not None:
        query = query.filter(CommandMeeting.start_time <= date_to)
    return (
        query.order_by(CommandMeeting.start_time.desc(), CommandMeeting.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete(db: Session, obj: CommandMeeting) -> None:
    db.delete(obj)
    db.commit()


def add_attendees(
    db: Session, meeting_id: int, pairs: list[tuple[int, Optional[int]]]
) -> list[CommandMeetingAttendee]:
    created = []
    for user_id, unit_id in pairs:
        a = CommandMeetingAttendee(
            meeting_id=meeting_id, user_id=user_id, unit_id=unit_id
        )
        db.add(a)
        created.append(a)
    db.commit()
    for a in created:
        db.refresh(a)
    return created


def get_attendee(
    db: Session, meeting_id: int, user_id: int
) -> CommandMeetingAttendee | None:
    return (
        db.query(CommandMeetingAttendee)
        .filter(
            CommandMeetingAttendee.meeting_id == meeting_id,
            CommandMeetingAttendee.user_id == user_id,
        )
        .first()
    )


def delete_attendee(db: Session, attendee: CommandMeetingAttendee) -> None:
    db.delete(attendee)
    db.commit()
