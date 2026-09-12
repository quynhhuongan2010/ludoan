"""Repository cho Hệ thống Tin nhắn Tác chiến Nội bộ (v7.8.0, mở rộng v8.1.0)."""

from datetime import datetime
from typing import Dict, Iterable, List, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.chat import (
    ChatConversation,
    ChatMessage,
    ChatMessageReaction,
    ChatParticipant,
)


def find_direct_conversation(
    db: Session, user1_id: int, user2_id: int
) -> Optional[ChatConversation]:
    """Tìm cuộc hội thoại 1-1 giữa 2 người dùng đã tồn tại."""
    from sqlalchemy import select

    # Subquery: các conversation_id có user1_id
    sub = select(ChatParticipant.conversation_id).where(
        ChatParticipant.user_id == user1_id
    )
    # Lấy các conversation có type == 'direct' chứa cả user1_id và user2_id
    conv = (
        db.query(ChatConversation)
        .join(ChatParticipant, ChatParticipant.conversation_id == ChatConversation.id)
        .filter(
            ChatConversation.type == "direct",
            ChatConversation.id.in_(sub),
            ChatParticipant.user_id == user2_id,
        )
        .first()
    )
    return conv


def create_conversation(db: Session, conv: ChatConversation) -> ChatConversation:
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation(db: Session, conversation_id: int) -> Optional[ChatConversation]:
    return (
        db.query(ChatConversation)
        .filter(ChatConversation.id == conversation_id)
        .first()
    )


def rename_conversation(db: Session, conv: ChatConversation, name: str) -> ChatConversation:
    conv.name = name
    db.commit()
    db.refresh(conv)
    return conv


def add_participant(db: Session, participant: ChatParticipant) -> ChatParticipant:
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def list_participant_user_ids(db: Session, conversation_id: int) -> List[int]:
    """Danh sách user_id của mọi thành viên trong cuộc hội thoại (phục vụ đẩy realtime)."""
    rows = (
        db.query(ChatParticipant.user_id)
        .filter(ChatParticipant.conversation_id == conversation_id)
        .all()
    )
    return [r[0] for r in rows]


def list_participants(db: Session, conversation_id: int) -> List[ChatParticipant]:
    """Danh sách bản ghi thành viên (kèm quan hệ user) - phục vụ biên nhận đã đọc."""
    return (
        db.query(ChatParticipant)
        .filter(ChatParticipant.conversation_id == conversation_id)
        .order_by(ChatParticipant.joined_at)
        .all()
    )


def get_participant(
    db: Session, conversation_id: int, user_id: int
) -> Optional[ChatParticipant]:
    return (
        db.query(ChatParticipant)
        .filter(
            ChatParticipant.conversation_id == conversation_id,
            ChatParticipant.user_id == user_id,
        )
        .first()
    )


def remove_participant(db: Session, participant: ChatParticipant) -> None:
    db.delete(participant)
    db.commit()


def set_member_admin(
    db: Session, conversation_id: int, user_id: int, is_admin: bool
) -> Optional[ChatParticipant]:
    p = get_participant(db, conversation_id, user_id)
    if p:
        p.is_admin = is_admin
        db.commit()
        db.refresh(p)
    return p


def set_participant_flag(
    db: Session, conversation_id: int, user_id: int, field: str, value: bool
) -> Optional[ChatParticipant]:
    """Bật/tắt một cờ tuỳ chọn của thành viên (`is_muted` | `is_archived`)."""
    if field not in {"is_muted", "is_archived"}:
        raise ValueError(f"Truong khong hop le: {field}")
    p = get_participant(db, conversation_id, user_id)
    if p:
        setattr(p, field, value)
        db.commit()
        db.refresh(p)
    return p


def delete_conversation(db: Session, conv: ChatConversation) -> None:
    """Xoá cứng cuộc hội thoại; cascade xoá luôn participants + messages."""
    db.delete(conv)
    db.commit()


def list_conversations_for_user(
    db: Session, user_id: int, include_archived: bool = False
) -> List[ChatConversation]:
    """Danh sách các cuộc trò chuyện người dùng tham gia, sắp xếp theo tin nhắn mới nhất.

    Nhóm chưa được duyệt (status != 'da_duyet') CHỈ hiện với người tạo nhóm —
    các thành viên khác không thấy cho tới khi được duyệt. Hội thoại mà thành
    viên đã tự lưu trữ (`ChatParticipant.is_archived`) bị ẩn trừ khi
    `include_archived=True`.
    """
    q = (
        db.query(ChatConversation)
        .join(ChatParticipant, ChatParticipant.conversation_id == ChatConversation.id)
        .filter(
            ChatParticipant.user_id == user_id,
            or_(
                ChatConversation.status == "da_duyet",
                ChatConversation.created_by_id == user_id,
            ),
        )
    )
    if not include_archived:
        q = q.filter(ChatParticipant.is_archived == False)  # noqa: E712
    return q.order_by(
        func.coalesce(ChatConversation.last_message_at, ChatConversation.created_at).desc()
    ).all()


def list_pending_groups(db: Session) -> List[ChatConversation]:
    """Danh sách nhóm đang chờ duyệt (mới nhất trước) — phục vụ người có quyền duyệt."""
    return (
        db.query(ChatConversation)
        .filter(
            ChatConversation.type == "group",
            ChatConversation.status == "cho_duyet",
        )
        .order_by(ChatConversation.created_at.desc())
        .all()
    )


def list_shared_contact_user_ids(db: Session, user_id: int) -> List[int]:
    """user_id của mọi quân nhân có chung ít nhất 1 hội thoại với `user_id`.

    Dùng để phát tín hiệu hiện diện (online/offline) đúng phạm vi liên quan.
    """
    from sqlalchemy import select

    my_conv_ids = select(ChatParticipant.conversation_id).where(
        ChatParticipant.user_id == user_id
    )
    rows = (
        db.query(ChatParticipant.user_id)
        .filter(
            ChatParticipant.conversation_id.in_(my_conv_ids),
            ChatParticipant.user_id != user_id,
        )
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def create_message(db: Session, msg: ChatMessage) -> ChatMessage:
    db.add(msg)
    # Cập nhật thời điểm và tóm tắt tin nhắn cuối của cuộc hội thoại
    conv = db.query(ChatConversation).filter(ChatConversation.id == msg.conversation_id).first()
    if conv:
        conv.last_message_at = msg.created_at or datetime.now()
        preview = msg.content[:100] + ("..." if len(msg.content) > 100 else "")
        conv.last_message_preview = preview
    db.commit()
    db.refresh(msg)
    return msg


def update_message(db: Session, msg: ChatMessage) -> ChatMessage:
    """Ghi lại thay đổi trên một tin nhắn đã có (sửa / thu hồi / ghim)."""
    db.commit()
    db.refresh(msg)
    return msg


def get_message(db: Session, message_id: int) -> Optional[ChatMessage]:
    return db.query(ChatMessage).filter(ChatMessage.id == message_id).first()


def get_message_in_conversation(
    db: Session, conversation_id: int, message_id: int
) -> Optional[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id,
            ChatMessage.conversation_id == conversation_id,
        )
        .first()
    )


def list_messages(
    db: Session, conversation_id: int, skip: int = 0, limit: int = 50
) -> List[ChatMessage]:
    """Lấy danh sách tin nhắn theo thứ tự thời gian tăng dần."""
    # Lấy tin nhắn mới nhất trước rồi đảo lại để render chat mượt mà
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    messages.reverse()
    return messages


def list_pinned_messages(db: Session, conversation_id: int) -> List[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.is_pinned == True,  # noqa: E712
            ChatMessage.is_recalled == False,  # noqa: E712
        )
        .order_by(ChatMessage.pinned_at.desc())
        .all()
    )


def search_messages(
    db: Session, conversation_id: int, q: str, skip: int = 0, limit: int = 50
) -> List[ChatMessage]:
    like = f"%{q}%"
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.is_recalled == False,  # noqa: E712
            ChatMessage.message_type == "user",
            ChatMessage.content.ilike(like),
        )
        .order_by(ChatMessage.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def search_messages_for_user(
    db: Session, user_id: int, q: str, limit: int = 50
) -> List[ChatMessage]:
    """Tìm tin nhắn trên mọi hội thoại mà `user_id` tham gia."""
    from sqlalchemy import select

    my_conv_ids = select(ChatParticipant.conversation_id).where(
        ChatParticipant.user_id == user_id
    )
    like = f"%{q}%"
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.conversation_id.in_(my_conv_ids),
            ChatMessage.is_recalled == False,  # noqa: E712
            ChatMessage.message_type == "user",
            ChatMessage.content.ilike(like),
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )


# --------------------------------------------------------------------- reactions


def get_reaction(
    db: Session, message_id: int, user_id: int, emoji: str
) -> Optional[ChatMessageReaction]:
    return (
        db.query(ChatMessageReaction)
        .filter(
            ChatMessageReaction.message_id == message_id,
            ChatMessageReaction.user_id == user_id,
            ChatMessageReaction.emoji == emoji,
        )
        .first()
    )


def add_reaction(db: Session, reaction: ChatMessageReaction) -> ChatMessageReaction:
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction


def remove_reaction(db: Session, reaction: ChatMessageReaction) -> None:
    db.delete(reaction)
    db.commit()


def list_reactions_for_messages(
    db: Session, message_ids: Iterable[int]
) -> Dict[int, List[ChatMessageReaction]]:
    ids = [i for i in message_ids]
    if not ids:
        return {}
    rows = (
        db.query(ChatMessageReaction)
        .filter(ChatMessageReaction.message_id.in_(ids))
        .order_by(ChatMessageReaction.created_at)
        .all()
    )
    grouped: Dict[int, List[ChatMessageReaction]] = {}
    for r in rows:
        grouped.setdefault(r.message_id, []).append(r)
    return grouped


# --------------------------------------------------------------------- reads / unread


def count_unread_for_participant(
    db: Session, conversation_id: int, last_read_at: Optional[datetime], current_user_id: int
) -> int:
    """Đếm số tin nhắn chưa đọc trong 1 cuộc hội thoại.

    Bỏ qua tin do chính mình gửi và tin hệ thống (đổi tên nhóm, thêm/bớt thành
    viên...) — tin hệ thống không làm tăng huy hiệu chưa đọc.
    """
    q = db.query(func.count(ChatMessage.id)).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.sender_id != current_user_id,
        ChatMessage.message_type != "system",
    )
    if last_read_at:
        q = q.filter(ChatMessage.created_at > last_read_at)
    return q.scalar() or 0


def _max_message_id(db: Session, conversation_id: int) -> int:
    return (
        db.query(func.coalesce(func.max(ChatMessage.id), 0))
        .filter(ChatMessage.conversation_id == conversation_id)
        .scalar()
        or 0
    )


def update_last_read(db: Session, conversation_id: int, user_id: int) -> Optional[int]:
    """Đánh dấu đã đọc tới tin mới nhất. Trả về `last_read_message_id` mới (hoặc None)."""
    participant = get_participant(db, conversation_id, user_id)
    if not participant:
        return None
    participant.last_read_at = datetime.now()
    participant.last_read_message_id = _max_message_id(db, conversation_id)
    db.commit()
    return participant.last_read_message_id


def count_total_unread_for_user(db: Session, user_id: int) -> int:
    """Tính tổng số tin nhắn chưa đọc trên toàn bộ các cuộc hội thoại của quân nhân."""
    participants = db.query(ChatParticipant).filter(ChatParticipant.user_id == user_id).all()
    total = 0
    for p in participants:
        total += count_unread_for_participant(
            db=db,
            conversation_id=p.conversation_id,
            last_read_at=p.last_read_at,
            current_user_id=user_id,
        )
    return total
