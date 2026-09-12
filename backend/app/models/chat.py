"""Mô hình dữ liệu cho Hệ thống Tin nhắn Tác chiến Nội bộ (Chat 1-1 & Chat Nhóm).

- v7.8.0  : cấu trúc gốc (hội thoại / thành viên / tin nhắn).
- v7.12.0 : duyệt nhóm (`status`, `review_note`, `reviewed_by_id`, `reviewed_at`).
- v8.1.0  : tương tác tin nhắn (trả lời, sửa, thu hồi, ghim, chuyển tiếp, tin hệ
            thống), thả cảm xúc (`chat_message_reactions`), tuỳ chọn theo thành
            viên (tắt thông báo / lưu trữ) và mốc đọc theo id tin nhắn.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import User

# Loại tin nhắn: 'user' = do quân nhân gửi; 'system' = tin hệ thống (đổi tên nhóm,
# thêm/đưa thành viên ra khỏi nhóm...) hiển thị căn giữa, không có tác giả thực.
MESSAGE_TYPE_USER = "user"
MESSAGE_TYPE_SYSTEM = "system"


class ChatConversation(Base):
    """Cuộc trò chuyện tác chiến / nghiệp vụ nội bộ (trực tiếp 1-1 hoặc nhóm kíp trực)."""

    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # direct (chat 1-1) | group (chat nhóm)
    type = Column(String(20), nullable=False, default="direct", index=True)
    # Tên nhóm (đối với group chat, hoặc để trống đối với direct chat)
    name = Column(String(200), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_message_at = Column(DateTime, nullable=True, index=True)
    last_message_preview = Column(String(255), nullable=True)
    is_archived = Column(Boolean, nullable=False, default=False)

    # Duyệt nhóm (v7.12.0). direct + nhóm do Ban chỉ huy (role 0..3) tạo -> "da_duyet"
    # ngay; nhóm do role 4..5 tạo -> "cho_duyet" tới khi role 0..1 duyệt; "tu_choi"
    # kèm lý do trong review_note nếu bị từ chối.
    status = Column(
        String(20), nullable=False, default="da_duyet", server_default="da_duyet", index=True
    )
    review_note = Column(String(500), nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_by = relationship(User, foreign_keys=[created_by_id])
    reviewed_by = relationship(User, foreign_keys=[reviewed_by_id])
    participants = relationship(
        "ChatParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatParticipant(Base):
    """Thành viên tham gia cuộc trò chuyện."""

    __tablename__ = "chat_participants"
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_chat_participant"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    joined_at = Column(DateTime, nullable=False, server_default=func.now())
    # Thời điểm đọc tin nhắn gần nhất để tính số lượng tin chưa đọc
    last_read_at = Column(DateTime, nullable=True)
    # id tin nhắn cuối cùng thành viên đã đọc (v8.1.0) - dùng cho biên nhận "đã xem"
    last_read_message_id = Column(Integer, nullable=False, default=0, server_default="0")
    # Tuỳ chọn theo thành viên (v8.1.0)
    is_muted = Column(Boolean, nullable=False, default=False, server_default="0")
    is_archived = Column(Boolean, nullable=False, default=False, server_default="0")

    conversation = relationship("ChatConversation", back_populates="participants")
    user = relationship(User, foreign_keys=[user_id])


class ChatMessage(Base):
    """Tin nhắn trong cuộc trò chuyện."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    attachment_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    # --- Tương tác tin nhắn (v8.1.0) ---
    message_type = Column(
        String(20), nullable=False, default=MESSAGE_TYPE_USER, server_default=MESSAGE_TYPE_USER
    )
    # Tham chiếu chéo (trả lời / chuyển tiếp) dùng ON DELETE SET NULL để không
    # chặn việc xoá cứng một hội thoại có tin đang được hội thoại khác trích dẫn.
    reply_to_id = Column(
        Integer, ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True
    )
    forwarded_from_id = Column(
        Integer, ForeignKey("chat_messages.id", ondelete="SET NULL"), nullable=True
    )
    is_edited = Column(Boolean, nullable=False, default=False, server_default="0")
    edited_at = Column(DateTime, nullable=True)
    is_recalled = Column(Boolean, nullable=False, default=False, server_default="0")
    recalled_at = Column(DateTime, nullable=True)
    is_pinned = Column(Boolean, nullable=False, default=False, server_default="0", index=True)
    pinned_at = Column(DateTime, nullable=True)
    pinned_by_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    conversation = relationship("ChatConversation", back_populates="messages")
    sender = relationship(User, foreign_keys=[sender_id])
    pinned_by = relationship(User, foreign_keys=[pinned_by_id])
    reply_to = relationship(
        "ChatMessage", remote_side=[id], foreign_keys=[reply_to_id], uselist=False
    )
    forwarded_from = relationship(
        "ChatMessage", remote_side=[id], foreign_keys=[forwarded_from_id], uselist=False
    )
    reactions = relationship(
        "ChatMessageReaction",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="ChatMessageReaction.created_at",
    )


class ChatMessageReaction(Base):
    """Một lượt thả cảm xúc của một quân nhân lên một tin nhắn (v8.1.0)."""

    __tablename__ = "chat_message_reactions"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", "emoji", name="uq_chat_message_reaction"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(
        Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    emoji = Column(String(16), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    message = relationship("ChatMessage", back_populates="reactions")
    user = relationship(User, foreign_keys=[user_id])
