"""
Script kiểm thử tự động Hệ thống Tin nhắn Tác chiến Nội bộ (Chat 1-1 & Chat Nhóm) (v7.8.0).
Bao gồm:
1. Khởi tạo hoặc tìm kiếm Chat 1-1 trực tiếp (idempotency, chặn chat với chính mình)
2. Khởi tạo nhóm chat nghiệp vụ / kíp trực tác chiến
3. Gửi tin nhắn 1-1 và tin nhắn nhóm
4. Kiểm tra logic đếm tin nhắn chưa đọc (unread_count) và đánh dấu đã đọc (mark_as_read)
5. Chặn quyền người ngoài nhóm: không được xem hoặc gửi tin vào nhóm không tham gia (HTTP 403)
6. Quản lý thành viên nhóm: thêm thành viên và rời nhóm
7. Kiểm thử trực tiếp qua API Route Handlers
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.models.user import User
from app.models.unit import Unit
from app.models.chat import ChatConversation, ChatMessage, ChatParticipant
from app.models.audit_log import AuditLog
from app.schemas.chat import (
    DirectChatCreate,
    GroupChatCreate,
    ChatMessageCreate,
    ChatAddMemberPayload,
)
from app.services import chat_service
from app.api.routes import chats as chat_routes


def test_chat_system_full_flow():
    print("=== BẮT ĐẦU KIỂM THỬ HỆ THỐNG TIN NHẮN TÁC CHIẾN NỘI BỘ (v7.8.0) ===")
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        # 1. Khởi tạo đơn vị và người dùng mẫu
        unit_bch = Unit(id=1, name="Ban chỉ huy Lữ đoàn", unit_kind="bch_lu_doan")
        unit_d1 = Unit(id=2, name="Tiểu đoàn 1", unit_kind="tieu_doan")
        unit_d2 = Unit(id=3, name="Tiểu đoàn 2", unit_kind="tieu_doan")
        db.add_all([unit_bch, unit_d1, unit_d2])
        db.commit()

        u1_lu_truong = User(
            id=1,
            username="lu_truong",
            hashed_password="hash",
            full_name="Đại tá Nguyễn Văn An",
            rank="Đại tá",
            position="Lữ đoàn trưởng",
            role=1,
            clearance=True,
            is_active=True,
            unit_id=1,
        )
        u2_d1_truong = User(
            id=2,
            username="d1_truong",
            hashed_password="hash",
            full_name="Trung tá Lê Văn Bình",
            rank="Trung tá",
            position="Tiểu đoàn trưởng d1",
            role=2,
            clearance=True,
            is_active=True,
            unit_id=2,
        )
        u3_tro_ly_tm = User(
            id=3,
            username="tro_ly_tm",
            hashed_password="hash",
            full_name="Đại úy Hoàng Đức Thắng",
            rank="Đại úy",
            position="Trợ lý Tác chiến",
            role=3,
            clearance=True,
            is_active=True,
            unit_id=2,
        )
        u4_ngoai_cuoc = User(
            id=4,
            username="chien_si_d2",
            hashed_password="hash",
            full_name="Thượng sĩ Vũ Văn Nam",
            rank="Thượng sĩ",
            position="Chiến sĩ TTLL d2",
            role=4,
            clearance=False,
            is_active=True,
            unit_id=3,
        )
        db.add_all([u1_lu_truong, u2_d1_truong, u3_tro_ly_tm, u4_ngoai_cuoc])
        db.commit()

        # ----------------------------------------------------------------------
        # TEST CASE 1: Mở hoặc khởi tạo chat 1-1 trực tiếp & tính Idempotency
        # ----------------------------------------------------------------------
        print("\n--- Test 1: Khởi tạo chat 1-1 trực tiếp & Kiểm tra tính duy nhất ---")
        chat_1_2 = chat_service.get_or_create_direct_chat(
            db=db, current_user=u1_lu_truong, recipient_id=u2_d1_truong.id
        )
        assert chat_1_2.id is not None
        assert chat_1_2.type == "direct"
        assert len(chat_1_2.participants) == 2
        print(f"-> Khởi tạo thành công cuộc trò chuyện 1-1 ID={chat_1_2.id} giữa Lữ trưởng và d1 trưởng")

        # Gọi lại từ phía d1 trưởng -> phải trả về đúng cuộc hội thoại ID cũ
        chat_2_1 = chat_service.get_or_create_direct_chat(
            db=db, current_user=u2_d1_truong, recipient_id=u1_lu_truong.id
        )
        assert chat_2_1.id == chat_1_2.id, "Lỗi: Không được tạo trùng cuộc trò chuyện 1-1!"
        print(f"-> Kiểm tra Idempotency đạt: d1_truong mở chat với lu_truong trả về đúng ID={chat_2_1.id}")

        # Chặn tự chat với chính mình
        self_chat_blocked = False
        try:
            chat_service.get_or_create_direct_chat(
                db=db, current_user=u1_lu_truong, recipient_id=u1_lu_truong.id
            )
        except HTTPException as e:
            if e.status_code == 400:
                self_chat_blocked = True
        assert self_chat_blocked, "Lỗi: Hệ thống phải chặn tạo chat với chính mình!"
        print("-> Đã chặn thành công tự chat với chính mình (400 Bad Request)")

        # ----------------------------------------------------------------------
        # TEST CASE 2: Tạo nhóm trao đổi kíp trực tác chiến
        # ----------------------------------------------------------------------
        print("\n--- Test 2: Tạo nhóm trao đổi nghiệp vụ / kíp trực tác chiến ---")
        group_payload = GroupChatCreate(
            name="Kíp trực ban Tác chiến SSCĐ d1",
            member_ids=[u2_d1_truong.id, u3_tro_ly_tm.id],
        )
        group_chat = chat_service.create_group_chat(
            db=db, current_user=u1_lu_truong, payload=group_payload
        )
        assert group_chat.id is not None
        assert group_chat.type == "group"
        assert group_chat.name == "Kíp trực ban Tác chiến SSCĐ d1"
        assert len(group_chat.participants) == 3  # u1 (admin), u2, u3
        print(f"-> Tạo nhóm chat thành công ID={group_chat.id} gồm {len(group_chat.participants)} thành viên")

        # ----------------------------------------------------------------------
        # TEST CASE 3: Gửi tin nhắn & kiểm tra số lượng chưa đọc (Unread Count)
        # ----------------------------------------------------------------------
        print("\n--- Test 3: Gửi tin nhắn nhóm & Kiểm tra đếm tin chưa đọc ---")
        msg_payload = ChatMessageCreate(
            content="Yêu cầu d1 kiểm tra phiên liên lạc vô tuyến điện lúc 14h00 hôm nay."
        )
        msg1 = chat_service.send_message(
            db=db, current_user=u1_lu_truong, conversation_id=group_chat.id, payload=msg_payload
        )
        assert msg1.id is not None
        assert msg1.is_me is True
        print(f"-> Lữ trưởng gửi tin nhắn ID={msg1.id} thành công")

        # Kiểm tra unread count:
        # Người gửi (u1) -> unread = 0
        unread_u1 = chat_service.get_total_unread_count(db=db, current_user=u1_lu_truong)
        assert unread_u1 == 0, f"Lỗi: Người gửi không thể có tin chưa đọc (nhận {unread_u1})"

        # Thành viên u2 -> unread = 1
        unread_u2 = chat_service.get_total_unread_count(db=db, current_user=u2_d1_truong)
        assert unread_u2 == 1, f"Lỗi: u2 phải có 1 tin chưa đọc (nhận {unread_u2})"

        # Thành viên u3 -> unread = 1
        unread_u3 = chat_service.get_total_unread_count(db=db, current_user=u3_tro_ly_tm)
        assert unread_u3 == 1, f"Lỗi: u3 phải có 1 tin chưa đọc (nhận {unread_u3})"
        print(f"-> Unread count chính xác: u1={unread_u1}, u2={unread_u2}, u3={unread_u3}")

        # ----------------------------------------------------------------------
        # TEST CASE 4: Đọc tin nhắn & Cập nhật trạng thái đã xem
        # ----------------------------------------------------------------------
        print("\n--- Test 4: Đọc tin nhắn & Đánh dấu đã đọc ---")
        # u2 xem tin nhắn trong nhóm
        messages_u2 = chat_service.get_conversation_messages(
            db=db, current_user=u2_d1_truong, conversation_id=group_chat.id
        )
        assert len(messages_u2) == 1
        assert messages_u2[0].is_me is False
        assert messages_u2[0].sender_name == "Đại tá Nguyễn Văn An"

        # Sau khi u2 xem, unread của u2 phải về 0
        unread_u2_after = chat_service.get_total_unread_count(db=db, current_user=u2_d1_truong)
        assert unread_u2_after == 0, f"Lỗi: Sau khi đọc tin, unread phải bằng 0 (nhận {unread_u2_after})"
        # Trong khi u3 chưa xem thì vẫn là 1
        assert chat_service.get_total_unread_count(db=db, current_user=u3_tro_ly_tm) == 1
        print("-> Đánh dấu đã đọc và cập nhật unread_count hoạt động hoàn hảo!")

        # ----------------------------------------------------------------------
        # TEST CASE 5: Chặn bảo mật người ngoài nhóm (HTTP 403)
        # ----------------------------------------------------------------------
        print("\n--- Test 5: Chặn bảo mật người dùng ngoài nhóm xem hoặc gửi tin ---")
        blocked_view = False
        try:
            chat_service.get_conversation_messages(
                db=db, current_user=u4_ngoai_cuoc, conversation_id=group_chat.id
            )
        except HTTPException as e:
            if e.status_code == 403:
                blocked_view = True
        assert blocked_view, "Lỗi: Người ngoài nhóm không được phép xem tin nhắn!"

        blocked_send = False
        try:
            chat_service.send_message(
                db=db,
                current_user=u4_ngoai_cuoc,
                conversation_id=group_chat.id,
                payload=ChatMessageCreate(content="Tin nhắn xâm nhập trái phép"),
            )
        except HTTPException as e:
            if e.status_code == 403:
                blocked_send = True
        assert blocked_send, "Lỗi: Người ngoài nhóm không được phép gửi tin nhắn vào nhóm!"
        print("-> Đã chặn 403 thành công mọi hành vi truy cập trái phép của người ngoài nhóm!")

        # ----------------------------------------------------------------------
        # TEST CASE 6: Quản lý thành viên (Thêm vào nhóm & Rời nhóm)
        # ----------------------------------------------------------------------
        print("\n--- Test 6: Quản lý thành viên nhóm ---")
        # Admin (u1) thêm u4 vào nhóm
        updated_group = chat_service.add_member_to_group(
            db=db, current_user=u1_lu_truong, conversation_id=group_chat.id, new_user_id=u4_ngoai_cuoc.id
        )
        assert len(updated_group.participants) == 4
        print(f"-> Thêm u4 vào nhóm thành công, tổng thành viên: {len(updated_group.participants)}")

        # u4 tự rời nhóm
        chat_service.remove_member_from_group(
            db=db, current_user=u4_ngoai_cuoc, conversation_id=group_chat.id, target_user_id=u4_ngoai_cuoc.id
        )
        p_check = db.query(ChatParticipant).filter(
            ChatParticipant.conversation_id == group_chat.id,
            ChatParticipant.user_id == u4_ngoai_cuoc.id,
        ).first()
        assert p_check is None
        print("-> u4 tự rời nhóm thành công")

        # ----------------------------------------------------------------------
        # TEST CASE 7: Kiểm thử trực tiếp Route Handlers API (Contract & Serialization)
        # ----------------------------------------------------------------------
        print("\n--- Test 7: Kiểm thử trực tiếp qua Route Handlers API ---")
        # GET /chats
        conv_list = chat_routes.list_conversations(db=db, current_user=u1_lu_truong)
        assert len(conv_list) >= 2  # 1 chat 1-1, 1 chat group
        print(f"-> GET /chats trả về {len(conv_list)} cuộc hội thoại")

        # GET /chats/unread-count
        unread_res = chat_routes.get_unread_count(db=db, current_user=u3_tro_ly_tm)
        assert unread_res.total_unread == 1
        print(f"-> GET /chats/unread-count trả về total_unread={unread_res.total_unread}")

        # POST /chats/{id}/read  (route handler la async tu v8.1.0 - day bien nhan realtime)
        read_res = asyncio.run(
            chat_routes.mark_read(id=group_chat.id, db=db, current_user=u3_tro_ly_tm)
        )
        assert read_res.get("ok") is True
        assert chat_service.get_total_unread_count(db=db, current_user=u3_tro_ly_tm) == 0
        print("-> POST /chats/{id}/read đánh dấu đọc thành công")

        print("\n=== TOÀN BỘ KIỂM THỬ HỆ THỐNG TIN NHẮN TÁC CHIẾN (v7.8.0) THÀNH CÔNG 100%! ===")

    finally:
        db.close()


if __name__ == "__main__":
    test_chat_system_full_flow()
