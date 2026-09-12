"""Route API cho Hệ thống Tin nhắn Tác chiến & Chat trực tiếp, Chat nhóm.

- v7.8.0  : hội thoại / tin nhắn / thành viên / unread.
- v7.10.0 : kênh WebSocket thời gian thực `/chats/ws`.
- v7.12.0 : duyệt nhóm chat.
- v8.1.0  : trả lời / sửa / thu hồi / ghim / chuyển tiếp tin nhắn, thả cảm xúc,
            tìm kiếm, tắt thông báo, lưu trữ, biên nhận đã đọc, "đang soạn tin",
            hiện diện online.
"""

import json
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, resolve_ws_user
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.uploads import (
    ARCHIVE_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    ext_of,
    save_upload,
)
from app.core.ws_manager import manager as ws_manager
from app.models.user import User
from app.repositories import chat_repository as chat_repo
from app.schemas.chat import (
    ArchivePayload,
    ChatAddMemberPayload,
    ChatConversationOut,
    ChatForwardPayload,
    ChatMessageCreate,
    ChatMessageEditPayload,
    ChatMessageOut,
    ChatMessagePinPayload,
    ChatReactionPayload,
    ChatUnreadCountResponse,
    DirectChatCreate,
    GroupChatCreate,
    GroupRenamePayload,
    GroupReviewPayload,
    MemberRolePayload,
    MutePayload,
    ReadReceiptOut,
)
from app.services import chat_service

router = APIRouter(
    prefix="/chats",
    tags=["chats"],
    dependencies=[Depends(get_current_user)],
)

# Tệp đính kèm trong tin nhắn: ảnh + tài liệu + video + tệp nén.
_CHAT_ATTACH_EXT = (
    IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS | VIDEO_EXTENSIONS | ARCHIVE_EXTENSIONS
)
# Tệp video và tệp nén thường lớn -> dùng hạn mức MAX_VIDEO_UPLOAD_MB thay vì MAX_UPLOAD_MB.
_CHAT_LARGE_EXT = VIDEO_EXTENSIONS | ARCHIVE_EXTENSIONS


# =====================================================================
# Cấp danh sách / tổng hợp
# =====================================================================


@router.get("", response_model=List[ChatConversationOut], status_code=status.HTTP_200_OK)
def list_conversations(
    archived: bool = Query(False, description="true = chỉ hiện hội thoại đã lưu trữ của người gọi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danh sách các cuộc trò chuyện tác chiến & trao đổi nghiệp vụ của quân nhân."""
    return chat_service.list_user_conversations(
        db=db, current_user=current_user, include_archived=archived
    )


@router.get("/unread-count", response_model=ChatUnreadCountResponse, status_code=status.HTTP_200_OK)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy tổng số tin nhắn chưa đọc của quân nhân để hiển thị huy hiệu trên thanh điều hướng."""
    total = chat_service.get_total_unread_count(db=db, current_user=current_user)
    return ChatUnreadCountResponse(total_unread=total)


@router.get("/search", response_model=List[ChatMessageOut], status_code=status.HTTP_200_OK)
def search_all_messages(
    q: str = Query(..., min_length=1, description="Từ khoá tìm kiếm"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tìm kiếm tin nhắn trên toàn bộ hội thoại mà quân nhân tham gia."""
    return chat_service.search_all(db=db, current_user=current_user, q=q, limit=limit)


@router.get(
    "/pending-groups",
    response_model=List[ChatConversationOut],
    status_code=status.HTTP_200_OK,
)
def list_pending_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danh sách nhóm chat đang chờ duyệt. Chỉ Quản trị hệ thống / Lữ trưởng / Chính uỷ (role 0-1) → 403 nếu khác."""
    return chat_service.list_pending_groups(db=db, current_user=current_user)


@router.post("/direct", response_model=ChatConversationOut, status_code=status.HTTP_200_OK)
def open_or_create_direct_chat(
    payload: DirectChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mở hoặc khởi tạo cuộc trò chuyện trực tiếp 1-1 với một đồng chí."""
    return chat_service.get_or_create_direct_chat(
        db=db, current_user=current_user, recipient_id=payload.recipient_id
    )


@router.post("/group", response_model=ChatConversationOut, status_code=status.HTTP_201_CREATED)
def create_group_chat(
    payload: GroupChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tạo nhóm trao đổi nghiệp vụ / nhóm kíp trực tác chiến mới."""
    return chat_service.create_group_chat(
        db=db, current_user=current_user, payload=payload
    )


# =====================================================================
# Tin nhắn trong một hội thoại
# =====================================================================


@router.get(
    "/{id}/messages/search",
    response_model=List[ChatMessageOut],
    status_code=status.HTTP_200_OK,
)
def search_conversation_messages(
    id: int,
    q: str = Query(..., min_length=1, description="Từ khoá tìm trong hội thoại"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tìm kiếm tin nhắn trong một hội thoại (yêu cầu là thành viên → 403)."""
    return chat_service.search_in_conversation(
        db=db, current_user=current_user, conversation_id=id, q=q, skip=skip, limit=limit
    )


@router.get("/{id}/messages", response_model=List[ChatMessageOut], status_code=status.HTTP_200_OK)
def get_messages(
    id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy lịch sử tin nhắn của cuộc trò chuyện (tự động cập nhật trạng thái đã đọc)."""
    return chat_service.get_conversation_messages(
        db=db, current_user=current_user, conversation_id=id, skip=skip, limit=limit
    )


@router.post("/{id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    id: int,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gửi tin nhắn mới vào cuộc trò chuyện, đẩy thời gian thực tới thành viên đang online."""
    message = chat_service.send_message(
        db=db, current_user=current_user, conversation_id=id, payload=payload
    )
    await chat_service.broadcast_new_message(db=db, conversation_id=id, message=message)
    return message


@router.post(
    "/{id}/messages/upload",
    response_model=ChatMessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message_with_file(
    id: int,
    content: str = Form("", description="Chú thích kèm tệp (tuỳ chọn)"),
    reply_to_id: Optional[int] = Form(None, description="ID tin nhắn được trả lời"),
    file: UploadFile = File(..., description="Ảnh / tài liệu / video đính kèm"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gửi tin nhắn kèm tệp đính kèm vào cuộc trò chuyện, đẩy thời gian thực tới thành viên online.

    Định dạng cho phép: ảnh (.jpg/.jpeg/.png/.webp/.gif), tài liệu
    (.pdf/.doc(x)/.xls(x)/.ppt(x)), video (.mp4/.webm/.ogg/.mov/.m4v) và
    tệp nén (.zip/.rar/.7z/.tar/.gz/.bz2). Video và tệp nén dùng hạn mức
    `MAX_VIDEO_UPLOAD_MB`, còn lại `MAX_UPLOAD_MB`. Sai định dạng / quá dung
    lượng / tệp rỗng → 400; không phải thành viên hội thoại → 403.
    """
    is_large = ext_of(file.filename or "") in _CHAT_LARGE_EXT
    saved = save_upload(
        file,
        subdir="chat",
        allowed_ext=_CHAT_ATTACH_EXT,
        max_mb=settings.MAX_VIDEO_UPLOAD_MB if is_large else None,
    )
    message = chat_service.send_file_message(
        db=db,
        current_user=current_user,
        conversation_id=id,
        content=content,
        saved=saved,
        reply_to_id=reply_to_id,
    )
    await chat_service.broadcast_new_message(db=db, conversation_id=id, message=message)
    return message


@router.patch(
    "/{id}/messages/{message_id}",
    response_model=ChatMessageOut,
    status_code=status.HTTP_200_OK,
)
async def edit_message(
    id: int,
    message_id: int,
    payload: ChatMessageEditPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sửa nội dung tin nhắn — chỉ người gửi; tin hệ thống / đã thu hồi → 409."""
    message = chat_service.edit_message(
        db=db,
        current_user=current_user,
        conversation_id=id,
        message_id=message_id,
        content=payload.content,
    )
    await chat_service.broadcast_message_edit(db=db, conversation_id=id, message=message)
    return message


@router.delete("/{id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def recall_message(
    id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Thu hồi tin nhắn — người gửi / quản trị viên nhóm / Ban chỉ huy. 403 nếu không đủ quyền."""
    chat_service.recall_message(
        db=db, current_user=current_user, conversation_id=id, message_id=message_id
    )
    await chat_service.broadcast_message_recall(
        db=db, conversation_id=id, message_id=message_id
    )


@router.post(
    "/{id}/messages/{message_id}/reactions",
    response_model=ChatMessageOut,
    status_code=status.HTTP_200_OK,
)
async def add_reaction(
    id: int,
    message_id: int,
    payload: ChatReactionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Thả một biểu tượng cảm xúc lên tin nhắn (idempotent nếu đã thả)."""
    message = chat_service.toggle_reaction(
        db=db,
        current_user=current_user,
        conversation_id=id,
        message_id=message_id,
        emoji=payload.emoji,
        add=True,
    )
    await chat_service.broadcast_message_reaction(db=db, conversation_id=id, message=message)
    return message


@router.delete(
    "/{id}/messages/{message_id}/reactions",
    response_model=ChatMessageOut,
    status_code=status.HTTP_200_OK,
)
async def remove_reaction(
    id: int,
    message_id: int,
    emoji: str = Query(..., min_length=1, max_length=16),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gỡ biểu tượng cảm xúc mà quân nhân đã thả trên tin nhắn."""
    message = chat_service.toggle_reaction(
        db=db,
        current_user=current_user,
        conversation_id=id,
        message_id=message_id,
        emoji=emoji,
        add=False,
    )
    await chat_service.broadcast_message_reaction(db=db, conversation_id=id, message=message)
    return message


@router.post(
    "/{id}/messages/{message_id}/pin",
    response_model=ChatMessageOut,
    status_code=status.HTTP_200_OK,
)
async def pin_message(
    id: int,
    message_id: int,
    payload: ChatMessagePinPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ghim / bỏ ghim tin nhắn. Nhóm: quản trị viên nhóm hoặc Ban chỉ huy → 403 nếu khác."""
    message = chat_service.set_pin(
        db=db,
        current_user=current_user,
        conversation_id=id,
        message_id=message_id,
        pinned=payload.pinned,
    )
    await chat_service.broadcast_message_pin(
        db=db, conversation_id=id, message_id=message_id, is_pinned=payload.pinned
    )
    return message


@router.post(
    "/{id}/messages/{message_id}/forward",
    response_model=ChatMessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def forward_message(
    id: int,
    message_id: int,
    payload: ChatForwardPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chuyển tiếp tin nhắn sang hội thoại đích (phải là thành viên cả hai → 403)."""
    message = chat_service.forward_message(
        db=db,
        current_user=current_user,
        conversation_id=id,
        message_id=message_id,
        target_conversation_id=payload.target_conversation_id,
    )
    await chat_service.broadcast_new_message(
        db=db, conversation_id=payload.target_conversation_id, message=message
    )
    return message


@router.get(
    "/{id}/pinned", response_model=List[ChatMessageOut], status_code=status.HTTP_200_OK
)
def list_pinned(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danh sách tin nhắn đã ghim trong hội thoại."""
    return chat_service.list_pinned(db=db, current_user=current_user, conversation_id=id)


# =====================================================================
# Đọc / biên nhận / tuỳ chọn hội thoại
# =====================================================================


@router.post("/{id}/read", status_code=status.HTTP_200_OK)
async def mark_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Đánh dấu đã đọc toàn bộ tin nhắn trong cuộc hội thoại + đẩy biên nhận realtime."""
    last_read_id = chat_service.mark_as_read(
        db=db, current_user=current_user, conversation_id=id
    )
    await chat_service.broadcast_read(
        db=db, conversation_id=id, current_user=current_user, last_read_message_id=last_read_id
    )
    return {"ok": True, "last_read_message_id": last_read_id}


@router.get(
    "/{id}/receipts", response_model=List[ReadReceiptOut], status_code=status.HTTP_200_OK
)
def get_receipts(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mốc đọc của từng thành viên trong hội thoại (hiển thị 'Đã xem')."""
    return chat_service.get_read_receipts(
        db=db, current_user=current_user, conversation_id=id
    )


@router.post("/{id}/mute", status_code=status.HTTP_200_OK)
def set_mute(
    id: int,
    payload: MutePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tắt / bật thông báo hội thoại cho chính người gọi."""
    chat_service.set_conversation_pref(
        db=db, current_user=current_user, conversation_id=id, muted=payload.muted
    )
    return {"ok": True, "is_muted": payload.muted}


@router.post("/{id}/archive", status_code=status.HTTP_200_OK)
def set_archive(
    id: int,
    payload: ArchivePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lưu trữ / bỏ lưu trữ hội thoại cho chính người gọi (ẩn khỏi danh sách mặc định)."""
    chat_service.set_conversation_pref(
        db=db, current_user=current_user, conversation_id=id, archived=payload.archived
    )
    return {"ok": True, "is_archived": payload.archived}


# =====================================================================
# Thành viên & quản trị nhóm
# =====================================================================


@router.post("/{id}/members", response_model=ChatConversationOut, status_code=status.HTTP_200_OK)
async def add_member(
    id: int,
    payload: ChatAddMemberPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Thêm một đồng chí vào nhóm trao đổi nghiệp vụ."""
    emitted: List[ChatMessageOut] = []
    conv = chat_service.add_member_to_group(
        db=db,
        current_user=current_user,
        conversation_id=id,
        new_user_id=payload.user_id,
        emitted=emitted,
    )
    for m in emitted:
        await chat_service.broadcast_new_message(db=db, conversation_id=id, message=m)
    return conv


@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_200_OK)
async def remove_member(
    id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rời nhóm (tự mình) hoặc xoá thành viên khác (người tạo nhóm / Quản trị hệ thống)."""
    emitted: List[ChatMessageOut] = []
    chat_service.remove_member_from_group(
        db=db,
        current_user=current_user,
        conversation_id=id,
        target_user_id=user_id,
        emitted=emitted,
    )
    for m in emitted:
        await chat_service.broadcast_new_message(db=db, conversation_id=id, message=m)
    return {"ok": True}


@router.patch(
    "/{id}/members/{user_id}/role",
    response_model=ChatConversationOut,
    status_code=status.HTTP_200_OK,
)
def set_member_role(
    id: int,
    user_id: int,
    payload: MemberRolePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Phong / gỡ quản trị viên nhóm — người tạo nhóm hoặc Ban chỉ huy. 409 nếu là người tạo nhóm."""
    return chat_service.set_member_admin(
        db=db,
        current_user=current_user,
        conversation_id=id,
        target_user_id=user_id,
        make_admin=payload.is_admin,
    )


@router.patch("/{id}", response_model=ChatConversationOut, status_code=status.HTTP_200_OK)
async def rename_group(
    id: int,
    payload: GroupRenamePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Đổi tên nhóm — quản trị viên nhóm hoặc Ban chỉ huy. Sinh 1 tin hệ thống."""
    emitted: List[ChatMessageOut] = []
    conv = chat_service.rename_group(
        db=db, current_user=current_user, conversation_id=id, name=payload.name, emitted=emitted
    )
    for m in emitted:
        await chat_service.broadcast_new_message(db=db, conversation_id=id, message=m)
    return conv


@router.post("/{id}/review", response_model=ChatConversationOut, status_code=status.HTTP_200_OK)
def review_group(
    id: int,
    payload: GroupReviewPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Duyệt / từ chối nhóm chờ duyệt. Quyền: role 0-1 → 403 nếu khác; 409 nếu nhóm không ở trạng thái chờ; 400 nếu từ chối mà thiếu lý do."""
    return chat_service.review_group(
        db=db,
        current_user=current_user,
        conversation_id=id,
        approve=payload.approve,
        note=payload.note,
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xoá cứng nhóm chat (kèm tin nhắn + tệp đính kèm). Quyền: người tạo nhóm hoặc Quản trị hệ thống (role 0) → 403 nếu khác."""
    chat_service.delete_group(db=db, current_user=current_user, conversation_id=id)


# ---------------------------------------------------------------------------
# KENH THOI GIAN THUC (WebSocket native FastAPI - KHONG dung Socket.IO)
# ---------------------------------------------------------------------------
# Router rieng, KHONG gan `Depends(get_current_user)` vi WebSocket cua trinh
# duyet khong gui header Authorization -> xac thuc bang token o query-string.
# WebSocket route khong xuat hien trong openapi.yaml (OpenAPI khong mo ta WS).
ws_router = APIRouter(tags=["chats-realtime"])


@ws_router.websocket("/chats/ws")
async def chat_realtime(websocket: WebSocket, token: str = Query(default="")):
    """Kenh day tin nhan / su kien thoi gian thuc.

    - Client mo:  ws(s)://<host>/chats/ws?token=<JWT>
    - Server -> client:
        {"type": "ready", "user_id": N}
        {"type": "message:new",    "message": <ChatMessageOut>}
        {"type": "message:edit",   "message": <ChatMessageOut>}
        {"type": "message:recall", "conversation_id": C, "message_id": M}
        {"type": "message:react",  "conversation_id": C, "message_id": M, "reactions": [...]}
        {"type": "message:pin",    "conversation_id": C, "message_id": M, "is_pinned": bool}
        {"type": "read",     "conversation_id": C, "user_id": U, "last_read_message_id": M}
        {"type": "typing",   "conversation_id": C, "user_id": U, "user_name": "..."}
        {"type": "presence", "user_id": U, "online": bool}
        {"type": "pong"}
    - Client -> server:
        "ping"  (chuoi, giu ket noi song ~25s/lan)
        {"type": "ping"}
        {"type": "typing", "conversation_id": C}
    """
    with SessionLocal() as db:
        user = resolve_ws_user(db, token)
    user_id = user.id if user else None

    await websocket.accept()
    if user_id is None or user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    was_online = ws_manager.is_online(user_id)
    await ws_manager.connect(user_id, websocket)
    try:
        await websocket.send_json({"type": "ready", "user_id": user_id})
        if not was_online:
            with SessionLocal() as db:
                await chat_service.broadcast_presence(db, user_id, True)

        while True:
            text = await websocket.receive_text()
            if text == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            try:
                data = json.loads(text)
            except (ValueError, TypeError):
                continue
            if not isinstance(data, dict):
                continue

            msg_type = data.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "typing":
                conv_id = data.get("conversation_id")
                if isinstance(conv_id, int):
                    with SessionLocal() as db:
                        if chat_repo.get_participant(db, conv_id, user_id):
                            await chat_service.broadcast_typing(db, conv_id, user)
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(user_id, websocket)
        if not ws_manager.is_online(user_id):
            with SessionLocal() as db:
                await chat_service.broadcast_presence(db, user_id, False)
