from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import can_access_command_channel, is_command_level
from app.core.uploads import SavedFile
from app.models.command_thread import CommandMessage, CommandThread
from app.models.user import User
from app.repositories import command_thread_repository as repo
from app.schemas.command_thread import (
    CommandMessageOut,
    CommandThreadCreate,
    CommandThreadDetailOut,
    CommandThreadOut,
)

_NOT_FOUND = "Không tìm thấy luồng trao đổi"
_FORBIDDEN = "Bạn không có quyền truy cập Kênh chuyên BCH & Cấp uỷ (yêu cầu quyền MẬT)"


def _require_channel(user: User) -> None:
    if not can_access_command_channel(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_FORBIDDEN)


def _msg_out(m: CommandMessage) -> CommandMessageOut:
    return CommandMessageOut(
        id=m.id,
        thread_id=m.thread_id,
        sender_id=m.sender_id,
        sender_full_name=m.sender.full_name if m.sender else "",
        body=m.body,
        attachment_url=m.attachment_url,
        created_at=m.created_at,
    )


def _thread_out(db: Session, t: CommandThread, current_user: User) -> CommandThreadOut:
    return CommandThreadOut(
        id=t.id,
        title=t.title,
        classification=t.classification,
        created_by_id=t.created_by_id,
        created_by_full_name=t.created_by.full_name if t.created_by else "",
        created_at=t.created_at,
        last_message_at=t.last_message_at,
        is_closed=t.is_closed,
        message_count=repo.count_messages(db, t.id),
        unread_count=repo.unread_count(db, t.id, current_user.id),
    )


def _get_or_404(db: Session, thread_id: int) -> CommandThread:
    t = repo.get_thread(db, thread_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return t


def list_threads(
    db: Session, current_user: User, *, skip: int = 0, limit: int = 100
) -> list[CommandThreadOut]:
    _require_channel(current_user)
    return [
        _thread_out(db, t, current_user)
        for t in repo.list_threads(db, skip=skip, limit=limit)
    ]


def create_thread(
    db: Session, current_user: User, payload: CommandThreadCreate
) -> CommandThreadOut:
    _require_channel(current_user)
    t = repo.create_thread(db, title=payload.title, created_by_id=current_user.id)
    return _thread_out(db, repo.get_thread(db, t.id), current_user)


def get_thread_detail(
    db: Session, current_user: User, thread_id: int, *, skip: int = 0, limit: int = 200
) -> CommandThreadDetailOut:
    _require_channel(current_user)
    t = _get_or_404(db, thread_id)
    repo.mark_read(db, thread_id, current_user.id)
    base = _thread_out(db, t, current_user)
    return CommandThreadDetailOut(
        **base.model_dump(),
        messages=[_msg_out(m) for m in repo.list_messages(db, thread_id, skip=skip, limit=limit)],
    )


def post_message(
    db: Session,
    current_user: User,
    thread_id: int,
    body: str,
    saved: Optional[SavedFile],
) -> CommandMessageOut:
    _require_channel(current_user)
    t = _get_or_404(db, thread_id)
    if t.is_closed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Luồng đã đóng, không thể gửi thêm"
        )
    body = (body or "").strip()
    if not body and saved is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nội dung tin nhắn trống"
        )
    msg = repo.add_message(
        db,
        thread_id=thread_id,
        sender_id=current_user.id,
        body=body,
        attachment_url=saved.url if saved else None,
    )
    repo.mark_read(db, thread_id, current_user.id)
    return _msg_out(
        db.query(CommandMessage).filter(CommandMessage.id == msg.id).first()
    )


def set_closed(
    db: Session, current_user: User, thread_id: int, is_closed: bool
) -> CommandThreadOut:
    _require_channel(current_user)
    if not is_command_level(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Ban chỉ huy được đóng / mở lại luồng",
        )
    t = _get_or_404(db, thread_id)
    return _thread_out(db, repo.set_closed(db, t, is_closed), current_user)
