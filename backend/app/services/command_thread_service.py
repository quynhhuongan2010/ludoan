from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import can_access_command_channel, command_thread_scope, is_command_level
from app.core.config import settings
from app.core.uploads import SavedFile, delete_secure_upload
from app.models.command_thread import (
    CommandMessage,
    CommandThread,
    CommandThreadDocument,
    CommandThreadMember,
    CommandThreadMinutes,
)
from app.models.user import User
from app.repositories import command_thread_repository as repo
from app.repositories import user_repository
from app.schemas.command_thread import (
    CommandMessageOut,
    CommandThreadCreate,
    CommandThreadDetailOut,
    CommandThreadDocumentOut,
    CommandThreadMinutesOut,
    CommandThreadOut,
    MemberOut,
)

_NOT_FOUND = "Không tìm thấy luồng trao đổi"
_FORBIDDEN = "Bạn không có quyền truy cập Kênh chuyên BCH & Cấp uỷ (yêu cầu quyền MẬT)"
_DOC_NOT_FOUND = "Không tìm thấy văn bản trong kho của luồng này"


def _require_channel(user: User) -> None:
    if not can_access_command_channel(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_FORBIDDEN)


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


def _member_out(m: CommandThreadMember) -> MemberOut:
    return MemberOut(
        user_id=m.user_id,
        full_name=m.user.full_name if m.user else "",
        unit_name=m.user.unit_name if m.user else None,
        added_at=m.added_at,
    )


def _doc_out(d: CommandThreadDocument) -> CommandThreadDocumentOut:
    return CommandThreadDocumentOut(
        id=d.id,
        thread_id=d.thread_id,
        title=d.title,
        visibility=d.visibility,
        file_url=d.file_url,
        file_name=d.file_name,
        file_size=d.file_size,
        content_type=d.content_type,
        uploaded_by_id=d.uploaded_by_id,
        uploaded_by_full_name=d.uploaded_by.full_name if d.uploaded_by else "",
        created_at=d.created_at,
    )


def _minutes_out(m: CommandThreadMinutes) -> CommandThreadMinutesOut:
    return CommandThreadMinutesOut(
        id=m.id,
        thread_id=m.thread_id,
        content=m.content,
        message_count=m.message_count,
        generated_by_id=m.generated_by_id,
        generated_by_full_name=m.generated_by.full_name if m.generated_by else "",
        generated_at=m.generated_at,
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
        member_count=repo.count_members(db, t.id),
    )


def _get_or_404(db: Session, thread_id: int) -> CommandThread:
    t = repo.get_thread(db, thread_id)
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return t


def _guard_visible(db: Session, current_user: User, thread_id: int) -> str:
    """Bat buoc `current_user` co trong pham vi xem luong. Tra ve scope ('all'/'member').

    Khong lo tinh ton tai cua luong voi nguoi ngoai thanh phan -> 404 thay vi 403.
    """
    scope = command_thread_scope(current_user)
    if scope is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_FORBIDDEN)
    if scope != "all" and not repo.is_member(db, thread_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return scope


def _can_manage_members(t: CommandThread, user: User) -> bool:
    return is_command_level(user) or t.created_by_id == user.id


# --------------------------------------------------------------------- threads


def list_threads(
    db: Session, current_user: User, *, skip: int = 0, limit: int = 100
) -> list[CommandThreadOut]:
    scope = command_thread_scope(current_user)
    if scope is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_FORBIDDEN)
    threads = repo.list_threads(
        db, user_id=current_user.id, scope_all=(scope == "all"), skip=skip, limit=limit
    )
    return [_thread_out(db, t, current_user) for t in threads]


def create_thread(
    db: Session, current_user: User, payload: CommandThreadCreate
) -> CommandThreadOut:
    _require_channel(current_user)
    members = _resolve_users(db, payload.member_user_ids)
    t = repo.create_thread(
        db,
        title=payload.title,
        created_by_id=current_user.id,
        member_user_ids=[u.id for u in members],
    )
    return _thread_out(db, repo.get_thread(db, t.id), current_user)


def get_thread_detail(
    db: Session, current_user: User, thread_id: int, *, skip: int = 0, limit: int = 200
) -> CommandThreadDetailOut:
    _guard_visible(db, current_user, thread_id)
    t = _get_or_404(db, thread_id)
    repo.mark_read(db, thread_id, current_user.id)
    base = _thread_out(db, t, current_user)
    return CommandThreadDetailOut(
        **base.model_dump(),
        messages=[_msg_out(m) for m in repo.list_messages(db, thread_id, skip=skip, limit=limit)],
        members=[_member_out(m) for m in repo.list_members(db, thread_id)],
    )


def post_message(
    db: Session,
    current_user: User,
    thread_id: int,
    body: str,
    saved: Optional[SavedFile],
) -> CommandMessageOut:
    _guard_visible(db, current_user, thread_id)
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
    _guard_visible(db, current_user, thread_id)
    if not is_command_level(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Ban chỉ huy được đóng / mở lại luồng",
        )
    t = _get_or_404(db, thread_id)
    return _thread_out(db, repo.set_closed(db, t, is_closed), current_user)


# --------------------------------------------------------------------- members


def add_members(
    db: Session, current_user: User, thread_id: int, user_ids: list[int]
) -> CommandThreadDetailOut:
    _guard_visible(db, current_user, thread_id)
    t = _get_or_404(db, thread_id)
    if not _can_manage_members(t, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tạo luồng hoặc Ban chỉ huy được gán thành phần",
        )
    members = _resolve_users(db, user_ids)
    repo.add_members(db, thread_id, [u.id for u in members])
    return get_thread_detail(db, current_user, thread_id)


def remove_member(db: Session, current_user: User, thread_id: int, user_id: int) -> None:
    _guard_visible(db, current_user, thread_id)
    t = _get_or_404(db, thread_id)
    if not _can_manage_members(t, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tạo luồng hoặc Ban chỉ huy được gỡ thành phần",
        )
    if user_id == t.created_by_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể gỡ người tạo luồng khỏi thành phần",
        )
    if not repo.remove_member(db, thread_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tài khoản này không thuộc thành phần"
        )


# --------------------------------------------------------------------- documents (kho van ban)


def list_documents(
    db: Session, current_user: User, thread_id: int
) -> list[CommandThreadDocumentOut]:
    _guard_visible(db, current_user, thread_id)
    can_see_private = is_command_level(current_user)
    out = []
    for d in repo.list_documents(db, thread_id):
        if d.visibility == "rieng" and not can_see_private and d.uploaded_by_id != current_user.id:
            continue
        out.append(_doc_out(d))
    return out


def upload_document(
    db: Session,
    current_user: User,
    thread_id: int,
    title: str,
    visibility: str,
    saved: SavedFile,
) -> CommandThreadDocumentOut:
    _guard_visible(db, current_user, thread_id)
    _get_or_404(db, thread_id)
    title = (title or "").strip() or saved.original_name
    doc = repo.add_document(
        db,
        thread_id=thread_id,
        title=title,
        visibility=visibility,
        uploaded_by_id=current_user.id,
        saved=saved,
    )
    return _doc_out(doc)


def _get_document_or_404(db: Session, thread_id: int, doc_id: int) -> CommandThreadDocument:
    d = repo.get_document(db, thread_id, doc_id)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_DOC_NOT_FOUND)
    return d


def _guard_document_visible(current_user: User, d: CommandThreadDocument) -> None:
    if d.visibility == "rieng" and not is_command_level(current_user) and d.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_DOC_NOT_FOUND)


def remove_document(db: Session, current_user: User, thread_id: int, doc_id: int) -> None:
    _guard_visible(db, current_user, thread_id)
    d = _get_document_or_404(db, thread_id, doc_id)
    if not (is_command_level(current_user) or d.uploaded_by_id == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tải lên hoặc Ban chỉ huy được xoá văn bản này",
        )
    delete_secure_upload(d.file_url)
    repo.remove_document(db, d)


def get_document(
    db: Session, current_user: User, thread_id: int, doc_id: int
) -> CommandThreadDocument:
    """Dung cho route tai file (FileResponse) - kiem tra day du quyen truoc khi tra ve."""
    _guard_visible(db, current_user, thread_id)
    d = _get_document_or_404(db, thread_id, doc_id)
    _guard_document_visible(current_user, d)
    return d


def get_download_target(
    db: Session, current_user: User, thread_id: int, doc_id: int
) -> tuple[Path, str, str]:
    d = get_document(db, current_user, thread_id, doc_id)
    if d.file_url.startswith("/secure/"):
        rel = d.file_url[len("/secure/") :]
        path = (settings.secure_upload_path / rel).resolve()
        if settings.secure_upload_path.resolve() in path.parents and path.is_file():
            return path, d.file_name, d.content_type or "application/octet-stream"

    rel = (
        d.file_url[len("/static/") :] if d.file_url.startswith("/static/") else d.file_url
    )
    path = (settings.upload_path / rel).resolve()
    if settings.upload_path.resolve() in path.parents and path.is_file():
        return path, d.file_name, d.content_type or "application/octet-stream"

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="File không tồn tại trên máy chủ"
    )


def get_message_attachment_download_target(
    db: Session, current_user: User, thread_id: int, message_id: int
) -> tuple[Path, str, str]:
    _guard_visible(db, current_user, thread_id)
    msg = (
        db.query(CommandMessage)
        .filter(CommandMessage.id == message_id, CommandMessage.thread_id == thread_id)
        .first()
    )
    if msg is None or not msg.attachment_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tệp đính kèm của tin nhắn",
        )
    if msg.attachment_url.startswith("/secure/"):
        rel = msg.attachment_url[len("/secure/") :]
        path = (settings.secure_upload_path / rel).resolve()
        if settings.secure_upload_path.resolve() in path.parents and path.is_file():
            return path, path.name, "application/octet-stream"

    rel = (
        msg.attachment_url[len("/static/") :]
        if msg.attachment_url.startswith("/static/")
        else msg.attachment_url
    )
    path = (settings.upload_path / rel).resolve()
    if settings.upload_path.resolve() in path.parents and path.is_file():
        return path, path.name, "application/octet-stream"

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="File không tồn tại trên máy chủ"
    )


# --------------------------------------------------------------------- bien ban (minutes)


def _compile_minutes(db: Session, t: CommandThread, current_user: User) -> tuple[str, int]:
    members = repo.list_members(db, t.id)
    messages = repo.list_messages(db, t.id, skip=0, limit=100000)
    all_docs = repo.list_documents(db, t.id)
    docs = [d for d in all_docs if d.visibility == "chung"]
    private_count = sum(1 for d in all_docs if d.visibility == "rieng")

    lines: list[str] = []
    lines.append("BIÊN BẢN CUỘC THẢO LUẬN")
    lines.append(f"Luồng trao đổi: {t.title}")
    lines.append(f"Người tạo biên bản: {current_user.full_name}")
    lines.append(f"Thời điểm tạo: {t.created_at.strftime('%H:%M %d/%m/%Y')} (bắt đầu luồng)")
    names = ", ".join(m.user.full_name for m in members if m.user) or "(chưa có)"
    lines.append(f"Thành phần tham gia ({len(members)}): {names}")
    lines.append("")
    lines.append(f"NỘI DUNG TRAO ĐỔI ({len(messages)} bước):")
    if not messages:
        lines.append("(chưa có tin nhắn nào)")
    for i, m in enumerate(messages, start=1):
        sender = m.sender.full_name if m.sender else "?"
        when = m.created_at.strftime("%H:%M %d/%m/%Y")
        lines.append(f"Bước {i} — [{when}] {sender}:")
        if m.body:
            lines.append(f"    {m.body}")
        if m.attachment_url:
            lines.append(f"    (đính kèm tệp: {m.attachment_url.rsplit('/', 1)[-1]})")
    lines.append("")
    lines.append(f"VĂN BẢN CHIA SẺ TRONG LUỒNG (kho chung, {len(docs)} tệp):")
    if not docs:
        lines.append("(không có)")
    for d in docs:
        when = d.created_at.strftime("%d/%m/%Y")
        uploader = d.uploaded_by.full_name if d.uploaded_by else "?"
        lines.append(f"- {d.title} ({d.file_name}) — tải lên bởi {uploader}, {when}")
    if private_count:
        lines.append(
            f"(còn {private_count} văn bản ở chế độ \"riêng\" không hiển thị trong biên bản này)"
        )
    lines.append("")
    lines.append(
        f"Trạng thái luồng tại thời điểm lập biên bản: {'đã đóng' if t.is_closed else 'đang mở'}."
    )
    return "\n".join(lines), len(messages)


def generate_minutes(
    db: Session, current_user: User, thread_id: int
) -> CommandThreadMinutesOut:
    _guard_visible(db, current_user, thread_id)
    t = _get_or_404(db, thread_id)
    content, message_count = _compile_minutes(db, t, current_user)
    row = repo.add_minutes(
        db,
        thread_id=thread_id,
        content=content,
        message_count=message_count,
        generated_by_id=current_user.id,
    )
    return _minutes_out(row)


def list_minutes(
    db: Session, current_user: User, thread_id: int
) -> list[CommandThreadMinutesOut]:
    _guard_visible(db, current_user, thread_id)
    _get_or_404(db, thread_id)
    return [_minutes_out(m) for m in repo.list_minutes(db, thread_id)]
