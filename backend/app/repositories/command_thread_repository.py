from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.command_thread import CommandMessage, CommandThread, CommandThreadRead


def create_thread(db: Session, *, title: str, created_by_id: int) -> CommandThread:
    thread = CommandThread(title=title, created_by_id=created_by_id)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def list_threads(db: Session, *, skip: int = 0, limit: int = 100) -> list[CommandThread]:
    recency = func.coalesce(CommandThread.last_message_at, CommandThread.created_at)
    return (
        db.query(CommandThread)
        .options(joinedload(CommandThread.created_by))
        .order_by(recency.desc(), CommandThread.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_thread(db: Session, thread_id: int) -> CommandThread | None:
    return (
        db.query(CommandThread)
        .options(joinedload(CommandThread.created_by))
        .filter(CommandThread.id == thread_id)
        .first()
    )


def set_closed(db: Session, thread: CommandThread, is_closed: bool) -> CommandThread:
    thread.is_closed = is_closed
    db.commit()
    db.refresh(thread)
    return thread


def list_messages(
    db: Session, thread_id: int, *, skip: int = 0, limit: int = 200
) -> list[CommandMessage]:
    return (
        db.query(CommandMessage)
        .options(joinedload(CommandMessage.sender))
        .filter(CommandMessage.thread_id == thread_id)
        .order_by(CommandMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_messages(db: Session, thread_id: int) -> int:
    return db.query(CommandMessage).filter(CommandMessage.thread_id == thread_id).count()


def add_message(
    db: Session, *, thread_id: int, sender_id: int, body: str, attachment_url: Optional[str]
) -> CommandMessage:
    msg = CommandMessage(
        thread_id=thread_id, sender_id=sender_id, body=body, attachment_url=attachment_url
    )
    db.add(msg)
    thread = db.get(CommandThread, thread_id)
    if thread is not None:
        thread.last_message_at = func.now()
    db.commit()
    db.refresh(msg)
    return msg


def _max_message_id(db: Session, thread_id: int) -> int:
    return (
        db.query(func.coalesce(func.max(CommandMessage.id), 0))
        .filter(CommandMessage.thread_id == thread_id)
        .scalar()
        or 0
    )


def get_read(db: Session, thread_id: int, user_id: int) -> CommandThreadRead | None:
    return (
        db.query(CommandThreadRead)
        .filter(
            CommandThreadRead.thread_id == thread_id,
            CommandThreadRead.user_id == user_id,
        )
        .first()
    )


def mark_read(db: Session, thread_id: int, user_id: int) -> None:
    last_id = _max_message_id(db, thread_id)
    row = get_read(db, thread_id, user_id)
    if row is None:
        db.add(
            CommandThreadRead(
                thread_id=thread_id,
                user_id=user_id,
                last_read_message_id=last_id,
                last_read_at=func.now(),
            )
        )
    else:
        row.last_read_message_id = max(row.last_read_message_id, last_id)
        row.last_read_at = func.now()
    db.commit()


def unread_count(db: Session, thread_id: int, user_id: int) -> int:
    row = get_read(db, thread_id, user_id)
    last_read = row.last_read_message_id if row is not None else 0
    return (
        db.query(CommandMessage)
        .filter(
            CommandMessage.thread_id == thread_id,
            CommandMessage.sender_id != user_id,
            CommandMessage.id > last_read,
        )
        .count()
    )
