"""Pydantic schemas cho Hệ thống Tin nhắn Tác chiến Nội bộ (v7.8.0, mở rộng v8.1.0)."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DirectChatCreate(BaseModel):
    recipient_id: int = Field(..., description="ID của đồng chí nhận tin nhắn trực tiếp")


class GroupChatCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Tên nhóm kíp trực hoặc nhóm công tác")
    member_ids: List[int] = Field(default_factory=list, description="Danh sách ID các thành viên ban đầu")


class GroupReviewPayload(BaseModel):
    approve: bool = Field(..., description="true = duyệt nhóm; false = từ chối")
    note: Optional[str] = Field(
        None, max_length=500, description="Lý do từ chối (BẮT BUỘC khi approve=false) hoặc ghi chú duyệt"
    )


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Nội dung tin nhắn")
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    reply_to_id: Optional[int] = Field(
        None, description="ID tin nhắn được trả lời (trích dẫn) trong cùng hội thoại"
    )


# --------------------------------------------------------------------- v8.1.0


class ChatMessageEditPayload(BaseModel):
    content: str = Field(..., min_length=1, description="Nội dung mới của tin nhắn")


class ChatReactionPayload(BaseModel):
    emoji: str = Field(..., min_length=1, max_length=16, description="Biểu tượng cảm xúc")


class ChatMessagePinPayload(BaseModel):
    pinned: bool = Field(..., description="true = ghim tin nhắn; false = bỏ ghim")


class ChatForwardPayload(BaseModel):
    target_conversation_id: int = Field(..., description="ID hội thoại đích để chuyển tiếp tin nhắn")


class GroupRenamePayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Tên nhóm mới")


class MemberRolePayload(BaseModel):
    is_admin: bool = Field(..., description="true = phong quản trị viên nhóm; false = gỡ")


class MutePayload(BaseModel):
    muted: bool = Field(..., description="true = tắt thông báo hội thoại; false = bật lại")


class ArchivePayload(BaseModel):
    archived: bool = Field(..., description="true = lưu trữ (ẩn khỏi danh sách); false = bỏ lưu trữ")


class ReactionOut(BaseModel):
    emoji: str
    count: int
    user_ids: List[int] = []
    mine: bool = False


class ReplyPreviewOut(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    content: str
    is_recalled: bool = False

    model_config = ConfigDict(from_attributes=True)


class ReadReceiptOut(BaseModel):
    user_id: int
    full_name: Optional[str] = None
    rank: Optional[str] = None
    last_read_message_id: int = 0
    last_read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------


class ChatParticipantOut(BaseModel):
    user_id: int
    username: str
    full_name: Optional[str] = None
    rank: Optional[str] = None
    position: Optional[str] = None
    unit_id: Optional[int] = None
    unit_name: Optional[str] = None
    is_admin: bool = False
    joined_at: datetime
    is_online: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChatMessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: str
    sender_rank: Optional[str] = None
    sender_position: Optional[str] = None
    content: str
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    created_at: datetime
    is_me: bool = False
    # v8.1.0
    message_type: str = "user"
    reply_to: Optional[ReplyPreviewOut] = None
    forwarded_from: Optional[ReplyPreviewOut] = None
    reactions: List[ReactionOut] = []
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    is_recalled: bool = False
    recalled_at: Optional[datetime] = None
    is_pinned: bool = False
    pinned_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ChatConversationOut(BaseModel):
    id: int
    type: str  # direct | group
    name: Optional[str] = None
    created_by_id: int
    created_at: datetime
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    unread_count: int = 0
    # Trạng thái duyệt nhóm: da_duyet | cho_duyet | tu_choi (direct luôn da_duyet)
    status: str = "da_duyet"
    review_note: Optional[str] = None
    reviewed_by_id: Optional[int] = None
    participants: List[ChatParticipantOut] = []
    # Đối với chat 1-1: thông tin của đồng chí đối thoại
    other_user: Optional[ChatParticipantOut] = None
    # v8.1.0 - tuỳ chọn của người gọi + hiện diện đối tác
    is_muted: bool = False
    is_archived: bool = False
    other_user_online: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChatAddMemberPayload(BaseModel):
    user_id: int = Field(..., description="ID của đồng chí được thêm vào nhóm")


class ChatUnreadCountResponse(BaseModel):
    total_unread: int = Field(..., description="Tổng số tin nhắn chưa đọc của người dùng")
