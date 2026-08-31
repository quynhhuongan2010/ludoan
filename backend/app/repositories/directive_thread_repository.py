from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.directive_thread import (
    DirectiveMessage,
    DirectiveThread,
    DirectiveThreadRead,
)


def create_thread(db: Session, *, unit_id: int, title: str, created_by_id: int) -> DirectiveThread:
    thread = DirectiveThread(unit_id=unit_id, title=title, created_by_id=created_by_id)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def list_threads(
    db: Session,
    *,
    unit_id: Optional[int] = None,
    unit_ids: Optional[list[int]] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[DirectiveThread]:
    query = db.query(DirectiveThread).options(
        joinedload(DirectiveThread.unit),
        joinedload(DirectiveThread.created_by),
    )
    if unit_id is not None:
        query = query.filter(DirectiveThread.unit_id == unit_id)
    if unit_ids is not None:
        query = query.filter(DirectiveThread.unit_id.in_(unit_ids or [-1]))
    # MySQL khong ho tro NULLS LAST -> dung coalesce(last_message_at, created_at)
    recency = func.coalesce(DirectiveThread.last_message_at, DirectiveThread.created_at)
    return (
        query.order_by(recency.desc(), DirectiveThread.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_thread(db: Session, thread_id: int) -> DirectiveThread | None:
    return (
        db.query(DirectiveThread)
        .options(joinedload(DirectiveThread.unit), joinedload(DirectiveThread.created_by))
        .filter(DirectiveThread.id == thread_id)
        .first()
    )


def set_closed(db: Session, thread: DirectiveThread, is_closed: bool) -> DirectiveThread:
    thread.is_closed = is_closed
    db.commit()
    db.refresh(thread)
    return thread


def list_messages(db: Session, thread_id: int, *, skip: int = 0, limit: int = 200) -> list[DirectiveMessage]:
    return (
        db.query(DirectiveMessage)
        .options(joinedload(DirectiveMessage.sender))
        .filter(DirectiveMessage.thread_id == thread_id)
        .order_by(DirectiveMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_messages(db: Session, thread_id: int) -> int:
    return db.query(DirectiveMessage).filter(DirectiveMessage.thread_id == thread_id).count()


def count_messages_by_thread(db: Session, thread_ids: list[int]) -> dict[int, int]:
    if not thread_ids:
        return {}
    rows = (
        db.query(DirectiveMessage.thread_id, func.count(DirectiveMessage.id))
        .filter(DirectiveMessage.thread_id.in_(thread_ids))
        .group_by(DirectiveMessage.thread_id)
        .all()
    )
    return {tid: n for tid, n in rows}


def add_message(
    db: Session, *, thread_id: int, sender_id: int, body: str, attachment_url: Optional[str]
) -> DirectiveMessage:
    msg = DirectiveMessage(
        thread_id=thread_id, sender_id=sender_id, body=body, attachment_url=attachment_url
    )
    db.add(msg)
    thread = db.get(DirectiveThread, thread_id)
    if thread is not None:
        thread.last_message_at = func.now()
    db.commit()
    db.refresh(msg)
    return msg


def get_read(db: Session, thread_id: int, user_id: int) -> DirectiveThreadRead | None:
    return (
        db.query(DirectiveThreadRead)
        .filter(
            DirectiveThreadRead.thread_id == thread_id,
            DirectiveThreadRead.user_id == user_id,
        )
        .first()
    )


def _max_message_id(db: Session, thread_id: int) -> int:
    return (
        db.query(func.coalesce(func.max(DirectiveMessage.id), 0))
        .filter(DirectiveMessage.thread_id == thread_id)
        .scalar()
        or 0
    )


def mark_read(db: Session, thread_id: int, user_id: int) -> None:
    last_id = _max_message_id(db, thread_id)
    row = get_read(db, thread_id, user_id)
    if row is None:
        db.add(
            DirectiveThreadRead(
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
        db.query(DirectiveMessage)
        .filter(
            DirectiveMessage.thread_id == thread_id,
            DirectiveMessage.sender_id != user_id,
            DirectiveMessage.id > last_read,
        )
        .count()
    )
