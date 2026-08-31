from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import (
    can_access_directive_channel,
    directive_thread_scope,
    is_command_level,
)
from app.core.uploads import SavedFile
from app.models.directive_thread import DirectiveMessage, DirectiveThread
from app.models.user import User
from app.repositories import directive_thread_repository as repo
from app.repositories import unit_repository
from app.schemas.directive_thread import (
    DirectiveMessageOut,
    DirectiveThreadCreate,
    DirectiveThreadDetailOut,
    DirectiveThreadOut,
)

_NOT_FOUND = "Không tìm thấy luồng trao đổi"


def _require_channel(user: User) -> None:
    if not can_access_directive_channel(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập Kênh Chỉ đạo – Báo cáo",
        )


def _msg_out(msg: DirectiveMessage) -> DirectiveMessageOut:
    return DirectiveMessageOut(
        id=msg.id,
        thread_id=msg.thread_id,
        sender_id=msg.sender_id,
        sender_full_name=msg.sender.full_name if msg.sender else "",
        body=msg.body,
        attachment_url=msg.attachment_url,
        created_at=msg.created_at,
    )


def _thread_out(db: Session, thread: DirectiveThread, current_user: User) -> DirectiveThreadOut:
    return DirectiveThreadOut(
        id=thread.id,
        unit_id=thread.unit_id,
        unit_name=thread.unit.name if thread.unit else f"#{thread.unit_id}",
        title=thread.title,
        created_by_id=thread.created_by_id,
        created_by_full_name=thread.created_by.full_name if thread.created_by else "",
        created_at=thread.created_at,
        last_message_at=thread.last_message_at,
        is_closed=thread.is_closed,
        message_count=repo.count_messages(db, thread.id),
        unread_count=repo.unread_count(db, thread.id, current_user.id),
    )


def _visible_thread_or_404(db: Session, thread_id: int, current_user: User) -> DirectiveThread:
    scope = directive_thread_scope(current_user)
    if scope is None:
        _require_channel(current_user)  # raises 403
    thread = repo.get_thread(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    if scope != "all" and thread.unit_id != scope:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return thread


def list_threads(
    db: Session,
    current_user: User,
    *,
    unit_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[DirectiveThreadOut]:
    _require_channel(current_user)
    scope = directive_thread_scope(current_user)
    if scope == "all":
        threads = repo.list_threads(db, unit_id=unit_id, skip=skip, limit=limit)
    else:
        if scope is None:
            return []
        threads = repo.list_threads(db, unit_id=scope, skip=skip, limit=limit)
    return [_thread_out(db, t, current_user) for t in threads]


def create_thread(
    db: Session, current_user: User, payload: DirectiveThreadCreate
) -> DirectiveThreadOut:
    _require_channel(current_user)
    scope = directive_thread_scope(current_user)

    if scope == "all":
        if payload.unit_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cần chọn đơn vị cho luồng trao đổi",
            )
        if unit_repository.get(db, payload.unit_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Đơn vị không tồn tại")
        unit_id = payload.unit_id
    else:
        unit_id = scope
        if unit_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tài khoản chưa được gán đơn vị — liên hệ quản trị",
            )

    thread = repo.create_thread(
        db, unit_id=unit_id, title=payload.title, created_by_id=current_user.id
    )
    thread = repo.get_thread(db, thread.id)
    return _thread_out(db, thread, current_user)


def get_thread_detail(
    db: Session, current_user: User, thread_id: int, *, skip: int = 0, limit: int = 200
) -> DirectiveThreadDetailOut:
    thread = _visible_thread_or_404(db, thread_id, current_user)
    repo.mark_read(db, thread_id, current_user.id)
    messages = repo.list_messages(db, thread_id, skip=skip, limit=limit)
    base = _thread_out(db, thread, current_user)
    return DirectiveThreadDetailOut(
        **base.model_dump(),
        messages=[_msg_out(m) for m in messages],
    )


def post_message(
    db: Session,
    current_user: User,
    thread_id: int,
    body: str,
    saved: Optional[SavedFile],
) -> DirectiveMessageOut:
    thread = _visible_thread_or_404(db, thread_id, current_user)
    if thread.is_closed:
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
    msg = db.query(DirectiveMessage).filter(DirectiveMessage.id == msg.id).first()
    return _msg_out(msg)


def set_closed(
    db: Session, current_user: User, thread_id: int, is_closed: bool
) -> DirectiveThreadOut:
    if not is_command_level(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Ban chỉ huy được đóng / mở lại luồng",
        )
    thread = repo.get_thread(db, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    thread = repo.set_closed(db, thread, is_closed)
    return _thread_out(db, thread, current_user)
