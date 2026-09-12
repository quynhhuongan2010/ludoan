"""Service nghiệp vụ Tin nhắn Tác chiến & Chat trực tiếp, Chat nhóm.

- v7.8.0 / v7.12.0 : hội thoại, thành viên, tin nhắn, duyệt nhóm.
- v8.1.0           : trả lời / sửa / thu hồi / ghim / chuyển tiếp / tin hệ thống,
                     thả cảm xúc, tìm kiếm, tắt thông báo, lưu trữ, biên nhận đã
                     đọc, hiện diện online + "đang soạn tin" qua WebSocket.
"""

from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.roles import can_approve_chat_group, is_admin, is_command
from app.core.uploads import SavedFile, delete_upload
from app.core.ws_manager import manager as ws_manager
from app.models.chat import (
    ChatConversation,
    ChatMessage,
    ChatMessageReaction,
    ChatParticipant,
)
from app.models.user import User
from app.repositories import chat_repository as repo
from app.schemas.chat import (
    ChatConversationOut,
    ChatMessageCreate,
    ChatMessageOut,
    ChatParticipantOut,
    GroupChatCreate,
    ReactionOut,
    ReadReceiptOut,
    ReplyPreviewOut,
)
from app.services import audit_log_service

# Trạng thái nhóm chat
GROUP_APPROVED = "da_duyet"
GROUP_PENDING = "cho_duyet"
GROUP_REJECTED = "tu_choi"

MESSAGE_TYPE_SYSTEM = "system"


# =====================================================================
# Helpers dùng chung
# =====================================================================


def _require_active_group(conv: Optional[ChatConversation]) -> None:
    """Chặn gửi tin / thêm người vào nhóm chưa được duyệt hoặc đã bị từ chối."""
    if conv is not None and conv.type == "group" and conv.status != GROUP_APPROVED:
        msg = (
            "Nhóm đang chờ chỉ huy duyệt — chưa trao đổi được."
            if conv.status == GROUP_PENDING
            else "Nhóm đã bị từ chối — không thể trao đổi."
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)


def _require_participant(db: Session, conversation_id: int, user_id: int) -> ChatParticipant:
    part = repo.get_participant(db, conversation_id, user_id)
    if not part:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Đồng chí không phải thành viên của cuộc trò chuyện này.",
        )
    return part


def _display_name(user: Optional[User]) -> str:
    if not user:
        return "Quân nhân"
    return user.full_name or user.username


def _reaction_out_list(
    reactions: List[ChatMessageReaction], current_user_id: int
) -> List[ReactionOut]:
    agg: Dict[str, ReactionOut] = {}
    for r in reactions:
        item = agg.get(r.emoji)
        if item is None:
            item = ReactionOut(emoji=r.emoji, count=0, user_ids=[], mine=False)
            agg[r.emoji] = item
        item.count += 1
        item.user_ids.append(r.user_id)
        if r.user_id == current_user_id:
            item.mine = True
    return list(agg.values())


def _reply_preview(m: Optional[ChatMessage]) -> Optional[ReplyPreviewOut]:
    if m is None:
        return None
    recalled = bool(m.is_recalled)
    return ReplyPreviewOut(
        id=m.id,
        sender_id=m.sender_id,
        sender_name=_display_name(m.sender),
        content="" if recalled else (m.content or ""),
        is_recalled=recalled,
    )


def _to_message_out(
    m: ChatMessage,
    current_user_id: int,
    reactions: Optional[List[ChatMessageReaction]] = None,
) -> ChatMessageOut:
    """Serialize thống nhất 1 tin nhắn (dùng cho mọi endpoint trả tin nhắn)."""
    sender = m.sender
    rx = reactions if reactions is not None else list(m.reactions or [])
    recalled = bool(m.is_recalled)
    return ChatMessageOut(
        id=m.id,
        conversation_id=m.conversation_id,
        sender_id=m.sender_id,
        sender_name=_display_name(sender),
        sender_rank=sender.rank if sender else None,
        sender_position=sender.position if sender else None,
        content="" if recalled else (m.content or ""),
        attachment_url=None if recalled else m.attachment_url,
        attachment_name=None if recalled else m.attachment_name,
        created_at=m.created_at,
        is_me=(m.sender_id == current_user_id),
        message_type=m.message_type or "user",
        reply_to=_reply_preview(m.reply_to),
        forwarded_from=_reply_preview(m.forwarded_from),
        reactions=_reaction_out_list(rx, current_user_id),
        is_edited=bool(m.is_edited),
        edited_at=m.edited_at,
        is_recalled=recalled,
        recalled_at=m.recalled_at,
        is_pinned=bool(m.is_pinned),
        pinned_at=m.pinned_at,
    )


def _messages_out(
    db: Session, messages: List[ChatMessage], current_user_id: int
) -> List[ChatMessageOut]:
    reactions_map = repo.list_reactions_for_messages(db, [m.id for m in messages])
    return [
        _to_message_out(m, current_user_id, reactions_map.get(m.id, []))
        for m in messages
    ]


def _to_participant_out(p: ChatParticipant) -> ChatParticipantOut:
    user = p.user
    unit_name = user.unit.name if user and user.unit else None
    return ChatParticipantOut(
        user_id=p.user_id,
        username=user.username if user else f"user_{p.user_id}",
        full_name=user.full_name if user else None,
        rank=user.rank if user else None,
        position=user.position if user else None,
        unit_id=user.unit_id if user else None,
        unit_name=unit_name,
        is_admin=p.is_admin,
        joined_at=p.joined_at,
        is_online=ws_manager.is_online(p.user_id),
    )


def _to_conversation_out(
    conv: ChatConversation, current_user_id: int, db: Session
) -> ChatConversationOut:
    participants_out = [_to_participant_out(p) for p in conv.participants]
    other_user = None

    # Tìm thông tin đối tác trong chat 1-1
    if conv.type == "direct":
        for p in participants_out:
            if p.user_id != current_user_id:
                other_user = p
                break

    # Tính số lượng tin chưa đọc + đọc cờ tuỳ chọn của người gọi
    current_part = next(
        (p for p in conv.participants if p.user_id == current_user_id), None
    )
    last_read_at = current_part.last_read_at if current_part else None
    unread_count = repo.count_unread_for_participant(
        db=db,
        conversation_id=conv.id,
        last_read_at=last_read_at,
        current_user_id=current_user_id,
    )

    conv_name = conv.name
    if conv.type == "direct" and other_user:
        conv_name = other_user.full_name or other_user.username

    return ChatConversationOut(
        id=conv.id,
        type=conv.type,
        name=conv_name,
        created_by_id=conv.created_by_id,
        created_at=conv.created_at,
        last_message_at=conv.last_message_at,
        last_message_preview=conv.last_message_preview,
        unread_count=unread_count,
        status=conv.status,
        review_note=conv.review_note,
        reviewed_by_id=conv.reviewed_by_id,
        participants=participants_out,
        other_user=other_user,
        is_muted=bool(current_part.is_muted) if current_part else False,
        is_archived=bool(current_part.is_archived) if current_part else False,
        other_user_online=bool(other_user.is_online) if other_user else False,
    )


def _post_system_message(
    db: Session, conversation_id: int, actor_id: int, text: str
) -> ChatMessage:
    """Ghi một tin hệ thống (đổi tên nhóm, thêm/đưa thành viên ra khỏi nhóm...)."""
    msg = ChatMessage(
        conversation_id=conversation_id,
        sender_id=actor_id,
        content=text,
        message_type=MESSAGE_TYPE_SYSTEM,
    )
    return repo.create_message(db, msg)


# =====================================================================
# Khởi tạo hội thoại
# =====================================================================


def get_or_create_direct_chat(
    db: Session, current_user: User, recipient_id: int
) -> ChatConversationOut:
    """Mở hoặc khởi tạo cuộc trò chuyện trực tiếp 1-1 giữa 2 quân nhân."""
    if current_user.id == recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tạo cuộc trò chuyện với chính mình.",
        )

    recipient = db.query(User).filter(User.id == recipient_id, User.is_active == True).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy quân nhân nhận tin nhắn hoặc tài khoản đã bị vô hiệu hoá.",
        )

    existing = repo.find_direct_conversation(db, current_user.id, recipient_id)
    if existing:
        return _to_conversation_out(existing, current_user.id, db)

    conv = ChatConversation(type="direct", name=None, created_by_id=current_user.id)
    created_conv = repo.create_conversation(db, conv)

    repo.add_participant(
        db,
        ChatParticipant(
            conversation_id=created_conv.id,
            user_id=current_user.id,
            is_admin=True,
            last_read_at=datetime.now(),
        ),
    )
    repo.add_participant(
        db,
        ChatParticipant(
            conversation_id=created_conv.id,
            user_id=recipient_id,
            is_admin=False,
            last_read_at=None,
        ),
    )

    db.refresh(created_conv)
    return _to_conversation_out(created_conv, current_user.id, db)


def create_group_chat(
    db: Session, current_user: User, payload: GroupChatCreate
) -> ChatConversationOut:
    """Tạo nhóm trao đổi nghiệp vụ / kíp trực tác chiến mới.

    Ban chỉ huy (role 0..3) tạo -> "da_duyet" dùng ngay. Role 4..5 tạo ->
    "cho_duyet": chỉ người tạo thấy nhóm cho tới khi role 0..1 duyệt.
    """
    approved = is_command(current_user)
    conv = ChatConversation(
        type="group",
        name=payload.name.strip(),
        created_by_id=current_user.id,
        status=GROUP_APPROVED if approved else GROUP_PENDING,
    )
    created_conv = repo.create_conversation(db, conv)

    repo.add_participant(
        db,
        ChatParticipant(
            conversation_id=created_conv.id,
            user_id=current_user.id,
            is_admin=True,
            last_read_at=datetime.now(),
        ),
    )

    unique_member_ids = set(payload.member_ids)
    unique_member_ids.discard(current_user.id)

    for uid in unique_member_ids:
        user_exists = db.query(User).filter(User.id == uid, User.is_active == True).first()
        if user_exists:
            repo.add_participant(
                db,
                ChatParticipant(
                    conversation_id=created_conv.id,
                    user_id=uid,
                    is_admin=False,
                    last_read_at=None,
                ),
            )

    db.refresh(created_conv)

    audit_log_service.record_action(
        db,
        action="CHAT_GROUP_CREATED" if approved else "CHAT_GROUP_REQUESTED",
        actor=current_user,
        target_type="chat_conversation",
        target_id=str(created_conv.id),
        target_name=created_conv.name,
        details=(
            f"Quân nhân {_display_name(current_user)} "
            f"{'tạo nhóm' if approved else 'xin tạo nhóm (chờ duyệt)'}: {created_conv.name} "
            f"với {len(unique_member_ids) + 1} thành viên"
        ),
    )

    return _to_conversation_out(created_conv, current_user.id, db)


def list_user_conversations(
    db: Session, current_user: User, include_archived: bool = False
) -> List[ChatConversationOut]:
    """Lấy danh sách các cuộc trò chuyện mà quân nhân tham gia."""
    convs = repo.list_conversations_for_user(
        db, current_user.id, include_archived=include_archived
    )
    return [_to_conversation_out(c, current_user.id, db) for c in convs]


# =====================================================================
# Tin nhắn
# =====================================================================


def get_conversation_messages(
    db: Session, current_user: User, conversation_id: int, skip: int = 0, limit: int = 50
) -> List[ChatMessageOut]:
    """Lấy lịch sử tin nhắn trong cuộc trò chuyện (yêu cầu là thành viên)."""
    _require_participant(db, conversation_id, current_user.id)
    repo.update_last_read(db, conversation_id, current_user.id)
    messages = repo.list_messages(db, conversation_id, skip=skip, limit=limit)
    return _messages_out(db, messages, current_user.id)


def _validate_reply_to(
    db: Session, conversation_id: int, reply_to_id: Optional[int]
) -> None:
    if reply_to_id is None:
        return
    target = repo.get_message_in_conversation(db, conversation_id, reply_to_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tin nhắn được trả lời trong hội thoại này.",
        )


def send_message(
    db: Session, current_user: User, conversation_id: int, payload: ChatMessageCreate
) -> ChatMessageOut:
    """Gửi tin nhắn mới vào cuộc trò chuyện."""
    _require_participant(db, conversation_id, current_user.id)
    _require_active_group(repo.get_conversation(db, conversation_id))
    _validate_reply_to(db, conversation_id, payload.reply_to_id)

    msg = ChatMessage(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=payload.content.strip(),
        attachment_url=payload.attachment_url,
        attachment_name=payload.attachment_name,
        reply_to_id=payload.reply_to_id,
    )
    saved = repo.create_message(db, msg)
    repo.update_last_read(db, conversation_id, current_user.id)
    return _to_message_out(saved, current_user.id, [])


def send_file_message(
    db: Session,
    current_user: User,
    conversation_id: int,
    content: str,
    saved: SavedFile,
    reply_to_id: Optional[int] = None,
) -> ChatMessageOut:
    """Gửi tin nhắn kèm tệp. `saved` là tệp đã được route lưu xuống đĩa.

    Nếu người gửi không thuộc hội thoại → xoá luôn tệp vừa lưu rồi raise 403.
    """
    participant = repo.get_participant(db, conversation_id, current_user.id)
    if not participant:
        delete_upload(saved.url)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Đồng chí không phải thành viên của cuộc trò chuyện này.",
        )
    conv = repo.get_conversation(db, conversation_id)
    if conv is not None and conv.type == "group" and conv.status != GROUP_APPROVED:
        delete_upload(saved.url)
        _require_active_group(conv)

    if reply_to_id is not None:
        target = repo.get_message_in_conversation(db, conversation_id, reply_to_id)
        if not target:
            delete_upload(saved.url)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy tin nhắn được trả lời trong hội thoại này.",
            )

    caption = (content or "").strip()
    msg = ChatMessage(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=caption or f"📎 {saved.original_name}",
        attachment_url=saved.url,
        attachment_name=saved.original_name,
        reply_to_id=reply_to_id,
    )
    saved_msg = repo.create_message(db, msg)
    repo.update_last_read(db, conversation_id, current_user.id)
    return _to_message_out(saved_msg, current_user.id, [])


def edit_message(
    db: Session, current_user: User, conversation_id: int, message_id: int, content: str
) -> ChatMessageOut:
    """Sửa nội dung một tin nhắn — chỉ người gửi, tin chưa thu hồi và không phải tin hệ thống."""
    _require_participant(db, conversation_id, current_user.id)
    m = repo.get_message_in_conversation(db, conversation_id, message_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tin nhắn.")
    if m.message_type == MESSAGE_TYPE_SYSTEM:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Không sửa được tin hệ thống.")
    if m.is_recalled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tin nhắn đã bị thu hồi.")
    if m.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người gửi mới sửa được tin nhắn.",
        )

    clean = content.strip()
    if not clean:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nội dung tin nhắn không được để trống.")

    m.content = clean
    m.is_edited = True
    m.edited_at = datetime.now()
    repo.update_message(db, m)
    return _to_message_out(m, current_user.id)


def recall_message(
    db: Session, current_user: User, conversation_id: int, message_id: int
) -> ChatMessageOut:
    """Thu hồi tin nhắn: người gửi, HOẶC quản trị viên nhóm, HOẶC Ban chỉ huy (role 0..3)."""
    participant = _require_participant(db, conversation_id, current_user.id)
    m = repo.get_message_in_conversation(db, conversation_id, message_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tin nhắn.")
    if m.message_type == MESSAGE_TYPE_SYSTEM:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Không thu hồi được tin hệ thống.")
    if m.is_recalled:
        return _to_message_out(m, current_user.id)

    allowed = (
        m.sender_id == current_user.id
        or participant.is_admin
        or is_command(current_user)
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không đủ quyền thu hồi tin nhắn này.",
        )

    if m.attachment_url:
        delete_upload(m.attachment_url)
    m.is_recalled = True
    m.recalled_at = datetime.now()
    m.content = ""
    m.attachment_url = None
    m.attachment_name = None
    m.is_pinned = False
    m.pinned_at = None
    m.pinned_by_id = None
    repo.update_message(db, m)
    return _to_message_out(m, current_user.id)


def toggle_reaction(
    db: Session,
    current_user: User,
    conversation_id: int,
    message_id: int,
    emoji: str,
    add: bool,
) -> ChatMessageOut:
    """Thêm (add=True) hoặc gỡ (add=False) một biểu tượng cảm xúc trên tin nhắn."""
    _require_participant(db, conversation_id, current_user.id)
    m = repo.get_message_in_conversation(db, conversation_id, message_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tin nhắn.")
    if m.is_recalled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tin nhắn đã bị thu hồi.")

    clean = emoji.strip()
    existing = repo.get_reaction(db, message_id, current_user.id, clean)
    if add and not existing:
        repo.add_reaction(
            db,
            ChatMessageReaction(message_id=message_id, user_id=current_user.id, emoji=clean),
        )
    elif not add and existing:
        repo.remove_reaction(db, existing)

    reactions = repo.list_reactions_for_messages(db, [message_id]).get(message_id, [])
    db.refresh(m)
    return _to_message_out(m, current_user.id, reactions)


def set_pin(
    db: Session,
    current_user: User,
    conversation_id: int,
    message_id: int,
    pinned: bool,
) -> ChatMessageOut:
    """Ghim / bỏ ghim tin nhắn. Nhóm: quản trị viên nhóm hoặc Ban chỉ huy. 1-1: cả hai bên."""
    participant = _require_participant(db, conversation_id, current_user.id)
    conv = repo.get_conversation(db, conversation_id)
    m = repo.get_message_in_conversation(db, conversation_id, message_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tin nhắn.")
    if m.is_recalled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Không ghim được tin đã thu hồi.")

    if conv is not None and conv.type == "group":
        if not participant.is_admin and not is_command(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ quản trị viên nhóm hoặc Ban chỉ huy mới ghim được tin trong nhóm.",
            )

    m.is_pinned = pinned
    m.pinned_at = datetime.now() if pinned else None
    m.pinned_by_id = current_user.id if pinned else None
    repo.update_message(db, m)
    return _to_message_out(m, current_user.id)


def list_pinned(
    db: Session, current_user: User, conversation_id: int
) -> List[ChatMessageOut]:
    _require_participant(db, conversation_id, current_user.id)
    messages = repo.list_pinned_messages(db, conversation_id)
    return _messages_out(db, messages, current_user.id)


def forward_message(
    db: Session,
    current_user: User,
    conversation_id: int,
    message_id: int,
    target_conversation_id: int,
) -> ChatMessageOut:
    """Chuyển tiếp một tin nhắn sang hội thoại khác (phải là thành viên CẢ HAI hội thoại)."""
    _require_participant(db, conversation_id, current_user.id)
    src = repo.get_message_in_conversation(db, conversation_id, message_id)
    if not src:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tin nhắn nguồn.")
    if src.is_recalled or src.message_type == MESSAGE_TYPE_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Không chuyển tiếp được tin đã thu hồi hoặc tin hệ thống.",
        )

    if target_conversation_id == conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hội thoại đích trùng với hội thoại nguồn.",
        )

    target_part = repo.get_participant(db, target_conversation_id, current_user.id)
    if not target_part:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Đồng chí không phải thành viên của hội thoại đích.",
        )
    _require_active_group(repo.get_conversation(db, target_conversation_id))

    new_msg = ChatMessage(
        conversation_id=target_conversation_id,
        sender_id=current_user.id,
        content=src.content,
        attachment_url=src.attachment_url,
        attachment_name=src.attachment_name,
        forwarded_from_id=src.id,
    )
    saved = repo.create_message(db, new_msg)
    repo.update_last_read(db, target_conversation_id, current_user.id)
    return _to_message_out(saved, current_user.id, [])


def search_in_conversation(
    db: Session,
    current_user: User,
    conversation_id: int,
    q: str,
    skip: int = 0,
    limit: int = 50,
) -> List[ChatMessageOut]:
    _require_participant(db, conversation_id, current_user.id)
    term = (q or "").strip()
    if not term:
        return []
    messages = repo.search_messages(db, conversation_id, term, skip=skip, limit=limit)
    return _messages_out(db, messages, current_user.id)


def search_all(
    db: Session, current_user: User, q: str, limit: int = 50
) -> List[ChatMessageOut]:
    term = (q or "").strip()
    if not term:
        return []
    messages = repo.search_messages_for_user(db, current_user.id, term, limit=limit)
    return _messages_out(db, messages, current_user.id)


# =====================================================================
# Realtime (WebSocket)
# =====================================================================


async def broadcast_new_message(
    db: Session, conversation_id: int, message: ChatMessageOut
) -> None:
    """Đẩy tin nhắn vừa lưu tới mọi thành viên đang mở kênh thời gian thực."""
    user_ids = repo.list_participant_user_ids(db, conversation_id)
    if not user_ids:
        return
    payload = message.model_dump(mode="json")
    payload["is_me"] = False
    await ws_manager.broadcast_to_users(
        user_ids, {"type": "message:new", "message": payload}
    )


async def _broadcast_to_conversation(
    db: Session, conversation_id: int, payload: dict
) -> None:
    user_ids = repo.list_participant_user_ids(db, conversation_id)
    if user_ids:
        await ws_manager.broadcast_to_users(user_ids, payload)


async def broadcast_message_edit(
    db: Session, conversation_id: int, message: ChatMessageOut
) -> None:
    payload = message.model_dump(mode="json")
    payload["is_me"] = False
    await _broadcast_to_conversation(
        db, conversation_id, {"type": "message:edit", "message": payload}
    )


async def broadcast_message_recall(
    db: Session, conversation_id: int, message_id: int
) -> None:
    await _broadcast_to_conversation(
        db,
        conversation_id,
        {"type": "message:recall", "conversation_id": conversation_id, "message_id": message_id},
    )


async def broadcast_message_reaction(
    db: Session, conversation_id: int, message: ChatMessageOut
) -> None:
    await _broadcast_to_conversation(
        db,
        conversation_id,
        {
            "type": "message:react",
            "conversation_id": conversation_id,
            "message_id": message.id,
            "reactions": [r.model_dump(mode="json") for r in message.reactions],
        },
    )


async def broadcast_message_pin(
    db: Session, conversation_id: int, message_id: int, is_pinned: bool
) -> None:
    await _broadcast_to_conversation(
        db,
        conversation_id,
        {
            "type": "message:pin",
            "conversation_id": conversation_id,
            "message_id": message_id,
            "is_pinned": is_pinned,
        },
    )


async def broadcast_read(
    db: Session, conversation_id: int, current_user: User, last_read_message_id: int
) -> None:
    await _broadcast_to_conversation(
        db,
        conversation_id,
        {
            "type": "read",
            "conversation_id": conversation_id,
            "user_id": current_user.id,
            "user_name": _display_name(current_user),
            "last_read_message_id": last_read_message_id,
        },
    )


async def broadcast_typing(
    db: Session, conversation_id: int, current_user: User
) -> None:
    user_ids = [
        uid
        for uid in repo.list_participant_user_ids(db, conversation_id)
        if uid != current_user.id
    ]
    if user_ids:
        await ws_manager.broadcast_to_users(
            user_ids,
            {
                "type": "typing",
                "conversation_id": conversation_id,
                "user_id": current_user.id,
                "user_name": _display_name(current_user),
            },
        )


async def broadcast_presence(db: Session, user_id: int, online: bool) -> None:
    targets = repo.list_shared_contact_user_ids(db, user_id)
    if targets:
        await ws_manager.broadcast_to_users(
            targets, {"type": "presence", "user_id": user_id, "online": online}
        )


# =====================================================================
# Đọc / biên nhận
# =====================================================================


def mark_as_read(db: Session, current_user: User, conversation_id: int) -> int:
    """Đánh dấu đã đọc toàn bộ tin nhắn; trả về `last_read_message_id` mới."""
    _require_participant(db, conversation_id, current_user.id)
    new_id = repo.update_last_read(db, conversation_id, current_user.id)
    return new_id or 0


def get_read_receipts(
    db: Session, current_user: User, conversation_id: int
) -> List[ReadReceiptOut]:
    """Danh sách mốc đọc của từng thành viên (phục vụ hiển thị 'Đã xem')."""
    _require_participant(db, conversation_id, current_user.id)
    parts = repo.list_participants(db, conversation_id)
    return [
        ReadReceiptOut(
            user_id=p.user_id,
            full_name=p.user.full_name if p.user else None,
            rank=p.user.rank if p.user else None,
            last_read_message_id=p.last_read_message_id or 0,
            last_read_at=p.last_read_at,
        )
        for p in parts
    ]


# =====================================================================
# Quản trị nhóm
# =====================================================================


def add_member_to_group(
    db: Session,
    current_user: User,
    conversation_id: int,
    new_user_id: int,
    emitted: Optional[List[ChatMessageOut]] = None,
) -> ChatConversationOut:
    """Thêm một đồng chí vào nhóm chat. Nếu truyền `emitted`, tin hệ thống sinh ra được đẩy vào đó."""
    conv = repo.get_conversation(db, conversation_id)
    if not conv or conv.type != "group":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ có thể thêm thành viên vào nhóm chat.",
        )

    _require_active_group(conv)

    curr_p = repo.get_participant(db, conversation_id, current_user.id)
    if not curr_p or (not curr_p.is_admin and not is_command(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ quản trị viên nhóm hoặc Ban Chỉ huy mới có quyền thêm thành viên.",
        )

    new_user = db.query(User).filter(User.id == new_user_id, User.is_active == True).first()
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy quân nhân cần thêm hoặc tài khoản đã bị vô hiệu hoá.",
        )

    existing = repo.get_participant(db, conversation_id, new_user_id)
    if not existing:
        repo.add_participant(
            db,
            ChatParticipant(
                conversation_id=conversation_id,
                user_id=new_user_id,
                is_admin=False,
                last_read_at=None,
            ),
        )
        sys_msg = _post_system_message(
            db,
            conversation_id,
            current_user.id,
            f"{_display_name(current_user)} đã thêm {_display_name(new_user)} vào nhóm",
        )
        if emitted is not None:
            emitted.append(_to_message_out(sys_msg, current_user.id, []))

    db.refresh(conv)
    return _to_conversation_out(conv, current_user.id, db)


def remove_member_from_group(
    db: Session,
    current_user: User,
    conversation_id: int,
    target_user_id: int,
    emitted: Optional[List[ChatMessageOut]] = None,
) -> None:
    """Rời nhóm hoặc xóa thành viên khỏi nhóm chat."""
    conv = repo.get_conversation(db, conversation_id)
    if not conv or conv.type != "group":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ áp dụng cho nhóm chat.",
        )

    curr_p = repo.get_participant(db, conversation_id, current_user.id)
    if not curr_p:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Đồng chí không thuộc nhóm chat này.",
        )

    is_self_leave = current_user.id == target_user_id
    can_manage = current_user.id == conv.created_by_id or is_admin(current_user)
    if not is_self_leave and not can_manage:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tạo nhóm hoặc Quản trị hệ thống mới xoá được thành viên khác.",
        )

    target_p = repo.get_participant(db, conversation_id, target_user_id)
    if target_p:
        target_user = target_p.user
        repo.remove_participant(db, target_p)
        text = (
            f"{_display_name(current_user)} đã rời nhóm"
            if is_self_leave
            else f"{_display_name(current_user)} đã đưa {_display_name(target_user)} ra khỏi nhóm"
        )
        sys_msg = _post_system_message(db, conversation_id, current_user.id, text)
        if emitted is not None:
            emitted.append(_to_message_out(sys_msg, current_user.id, []))


def rename_group(
    db: Session,
    current_user: User,
    conversation_id: int,
    name: str,
    emitted: Optional[List[ChatMessageOut]] = None,
) -> ChatConversationOut:
    """Đổi tên nhóm — quản trị viên nhóm hoặc Ban chỉ huy."""
    conv = repo.get_conversation(db, conversation_id)
    if not conv or conv.type != "group":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ đổi tên được nhóm chat.")

    participant = repo.get_participant(db, conversation_id, current_user.id)
    if not participant or (not participant.is_admin and not is_command(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ quản trị viên nhóm hoặc Ban chỉ huy mới đổi được tên nhóm.",
        )

    clean = name.strip()
    if len(clean) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên nhóm quá ngắn.")

    old_name = conv.name
    repo.rename_conversation(db, conv, clean)
    sys_msg = _post_system_message(
        db,
        conversation_id,
        current_user.id,
        f"{_display_name(current_user)} đổi tên nhóm thành «{clean}»",
    )
    if emitted is not None:
        emitted.append(_to_message_out(sys_msg, current_user.id, []))

    audit_log_service.record_action(
        db,
        action="CHAT_GROUP_RENAMED",
        actor=current_user,
        target_type="chat_conversation",
        target_id=str(conversation_id),
        target_name=clean,
        details=f"Đổi tên nhóm chat '{old_name}' -> '{clean}'",
    )
    db.refresh(conv)
    return _to_conversation_out(conv, current_user.id, db)


def set_member_admin(
    db: Session,
    current_user: User,
    conversation_id: int,
    target_user_id: int,
    make_admin: bool,
) -> ChatConversationOut:
    """Phong / gỡ quản trị viên nhóm — người tạo nhóm hoặc Ban chỉ huy."""
    conv = repo.get_conversation(db, conversation_id)
    if not conv or conv.type != "group":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ áp dụng cho nhóm chat.")

    if current_user.id != conv.created_by_id and not is_command(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tạo nhóm hoặc Ban chỉ huy mới phong/gỡ quản trị viên nhóm.",
        )

    if target_user_id == conv.created_by_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Không thể đổi quyền quản trị của người tạo nhóm.",
        )

    target_p = repo.get_participant(db, conversation_id, target_user_id)
    if not target_p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thành viên không có trong nhóm.",
        )

    repo.set_member_admin(db, conversation_id, target_user_id, make_admin)
    db.refresh(conv)
    return _to_conversation_out(conv, current_user.id, db)


def set_conversation_pref(
    db: Session,
    current_user: User,
    conversation_id: int,
    *,
    muted: Optional[bool] = None,
    archived: Optional[bool] = None,
) -> None:
    """Cập nhật cờ tuỳ chọn của CHÍNH người gọi trên hội thoại (tắt thông báo / lưu trữ)."""
    _require_participant(db, conversation_id, current_user.id)
    if muted is not None:
        repo.set_participant_flag(db, conversation_id, current_user.id, "is_muted", muted)
    if archived is not None:
        repo.set_participant_flag(db, conversation_id, current_user.id, "is_archived", archived)


# =====================================================================
# Duyệt nhóm (giữ nguyên từ v7.12.0)
# =====================================================================


def list_pending_groups(db: Session, current_user: User) -> List[ChatConversationOut]:
    if not can_approve_chat_group(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Quản trị hệ thống / Lữ trưởng / Chính uỷ mới xem được danh sách nhóm chờ duyệt.",
        )
    return [
        _to_conversation_out(c, current_user.id, db)
        for c in repo.list_pending_groups(db)
    ]


def review_group(
    db: Session,
    current_user: User,
    conversation_id: int,
    approve: bool,
    note: Optional[str],
) -> ChatConversationOut:
    if not can_approve_chat_group(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Quản trị hệ thống / Lữ trưởng / Chính uỷ mới có quyền duyệt nhóm.",
        )

    conv = repo.get_conversation(db, conversation_id)
    if not conv or conv.type != "group":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhóm chat.")
    if conv.status != GROUP_PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nhóm này không ở trạng thái chờ duyệt.",
        )

    clean_note = (note or "").strip()
    if not approve and not clean_note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phải nhập lý do khi từ chối nhóm.",
        )

    conv.status = GROUP_APPROVED if approve else GROUP_REJECTED
    conv.review_note = clean_note or None
    conv.reviewed_by_id = current_user.id
    conv.reviewed_at = datetime.now()
    db.commit()
    db.refresh(conv)

    audit_log_service.record_action(
        db,
        action="CHAT_GROUP_APPROVED" if approve else "CHAT_GROUP_REJECTED",
        actor=current_user,
        target_type="chat_conversation",
        target_id=str(conv.id),
        target_name=conv.name,
        details=(
            f"{'Duyệt' if approve else 'Từ chối'} nhóm '{conv.name}'"
            + (f" — lý do: {clean_note}" if clean_note else "")
        ),
    )
    return _to_conversation_out(conv, current_user.id, db)


def delete_group(db: Session, current_user: User, conversation_id: int) -> None:
    """Xoá cứng nhóm chat (kèm mọi tin nhắn + tệp đính kèm trên đĩa)."""
    conv = repo.get_conversation(db, conversation_id)
    if not conv or conv.type != "group":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhóm chat.")

    if current_user.id != conv.created_by_id and not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tạo nhóm hoặc Quản trị hệ thống mới xoá được nhóm.",
        )

    for m in list(conv.messages):
        if m.attachment_url:
            delete_upload(m.attachment_url)

    name = conv.name
    repo.delete_conversation(db, conv)

    audit_log_service.record_action(
        db,
        action="CHAT_GROUP_DELETED",
        actor=current_user,
        target_type="chat_conversation",
        target_id=str(conversation_id),
        target_name=name,
        details=f"Xoá nhóm chat '{name}' (xoá cứng toàn bộ tin nhắn + tệp đính kèm)",
    )


def get_total_unread_count(db: Session, current_user: User) -> int:
    return repo.count_total_unread_for_user(db, current_user.id)
