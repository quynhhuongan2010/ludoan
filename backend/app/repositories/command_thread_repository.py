from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.uploads import SavedFile
from app.models.command_thread import (
    CommandMessage,
    CommandThread,
    CommandThreadDocument,
    CommandThreadMember,
    CommandThreadMinutes,
    CommandThreadRead,
)

# --------------------------------------------------------------------- threads


def create_thread(
    db: Session, *, title: str, created_by_id: int, member_user_ids: Optional[list[int]] = None
) -> CommandThread:
    thread = CommandThread(title=title, created_by_id=created_by_id)
    db.add(thread)
    db.flush()  # can thread.id truoc khi tao thanh vien

    member_ids = set(member_user_ids or [])
    member_ids.add(created_by_id)  # nguoi tao luon la thanh vien
    for uid in member_ids:
        db.add(CommandThreadMember(thread_id=thread.id, user_id=uid))

    db.commit()
    db.refresh(thread)
    return thread


def list_threads(
    db: Session, *, user_id: int, scope_all: bool, skip: int = 0, limit: int = 100
) -> list[CommandThread]:
    """scope_all=True (BCH/admin): thay moi luong. False: chi luong da duoc gan lam thanh vien."""
    recency = func.coalesce(CommandThread.last_message_at, CommandThread.created_at)
    q = db.query(CommandThread).options(joinedload(CommandThread.created_by))
    if not scope_all:
        q = q.join(
            CommandThreadMember, CommandThreadMember.thread_id == CommandThread.id
        ).filter(CommandThreadMember.user_id == user_id)
    return q.order_by(recency.desc(), CommandThread.id.desc()).offset(skip).limit(limit).all()


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


# --------------------------------------------------------------------- members


def is_member(db: Session, thread_id: int, user_id: int) -> bool:
    return (
        db.query(CommandThreadMember)
        .filter(CommandThreadMember.thread_id == thread_id, CommandThreadMember.user_id == user_id)
        .first()
        is not None
    )


def list_members(db: Session, thread_id: int) -> list[CommandThreadMember]:
    return (
        db.query(CommandThreadMember)
        .options(joinedload(CommandThreadMember.user))
        .filter(CommandThreadMember.thread_id == thread_id)
        .order_by(CommandThreadMember.added_at.asc())
        .all()
    )


def count_members(db: Session, thread_id: int) -> int:
    return (
        db.query(CommandThreadMember).filter(CommandThreadMember.thread_id == thread_id).count()
    )


def add_members(db: Session, thread_id: int, user_ids: list[int]) -> None:
    existing = {
        m.user_id
        for m in db.query(CommandThreadMember)
        .filter(CommandThreadMember.thread_id == thread_id)
        .all()
    }
    for uid in user_ids:
        if uid not in existing:
            db.add(CommandThreadMember(thread_id=thread_id, user_id=uid))
    db.commit()


def remove_member(db: Session, thread_id: int, user_id: int) -> bool:
    row = (
        db.query(CommandThreadMember)
        .filter(CommandThreadMember.thread_id == thread_id, CommandThreadMember.user_id == user_id)
        .first()
    )
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


# --------------------------------------------------------------------- messages


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


# --------------------------------------------------------------------- documents (kho van ban)


def add_document(
    db: Session,
    *,
    thread_id: int,
    title: str,
    visibility: str,
    uploaded_by_id: int,
    saved: SavedFile,
) -> CommandThreadDocument:
    doc = CommandThreadDocument(
        thread_id=thread_id,
        title=title,
        visibility=visibility,
        file_url=saved.url,
        file_name=saved.original_name,
        file_size=saved.size,
        content_type=saved.content_type,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_documents(db: Session, thread_id: int) -> list[CommandThreadDocument]:
    return (
        db.query(CommandThreadDocument)
        .options(joinedload(CommandThreadDocument.uploaded_by))
        .filter(CommandThreadDocument.thread_id == thread_id)
        .order_by(CommandThreadDocument.created_at.desc())
        .all()
    )


def get_document(db: Session, thread_id: int, doc_id: int) -> CommandThreadDocument | None:
    return (
        db.query(CommandThreadDocument)
        .options(joinedload(CommandThreadDocument.uploaded_by))
        .filter(CommandThreadDocument.id == doc_id, CommandThreadDocument.thread_id == thread_id)
        .first()
    )


def remove_document(db: Session, doc: CommandThreadDocument) -> None:
    db.delete(doc)
    db.commit()


# --------------------------------------------------------------------- bien ban (minutes)


def add_minutes(
    db: Session, *, thread_id: int, content: str, message_count: int, generated_by_id: int
) -> CommandThreadMinutes:
    row = CommandThreadMinutes(
        thread_id=thread_id,
        content=content,
        message_count=message_count,
        generated_by_id=generated_by_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_minutes(db: Session, thread_id: int) -> list[CommandThreadMinutes]:
    return (
        db.query(CommandThreadMinutes)
        .options(joinedload(CommandThreadMinutes.generated_by))
        .filter(CommandThreadMinutes.thread_id == thread_id)
        .order_by(CommandThreadMinutes.generated_at.desc())
        .all()
    )
