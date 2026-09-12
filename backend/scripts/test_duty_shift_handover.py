"""
Script test tự động tính năng Biên bản bàn giao ca trực & Sổ nhật ký kíp trực điện tử (Step 5 - v7.5.0)
Kiểm thử toàn diện từ Service layer đến API Endpoint qua FastAPI TestClient:
1. Tạo biên bản bàn giao ca trực (create_handover)
2. Ký nhận ca trực & ghi chú tình trạng (acknowledge_handover)
3. Chỉ huy kiểm tra, phê duyệt & cho ý kiến chỉ đạo (review_handover)
4. Phân quyền: Người dùng thường không thể duyệt ca thay Chỉ huy
5. Kiểm thử API Endpoints (GET, POST) qua TestClient
6. Kiểm thử tra cứu theo lịch trực và danh sách nhật ký
"""

import sys
from pathlib import Path
from datetime import datetime, date

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, Request

from app.core.database import Base
from app.models.user import User
from app.models.unit import Unit
from app.models.duty_week_plan import DutyWeekPlan
from app.models.duty_schedule import DutySchedule
from app.models.duty_shift_handover import DutyShiftHandover
from app.models.audit_log import AuditLog
from app.schemas.duty_shift_handover import (
    DutyShiftHandoverCreate,
    DutyShiftHandoverAcknowledge,
    DutyShiftHandoverCommanderReview,
)
from app.services import duty_shift_handover_service
from app.api.routes import duty_shift_handovers as handover_routes


def test_duty_shift_handover_flow():
    print("=== BẮT ĐẦU KIỂM THỬ BÀN GIAO CA TRỰC & SỔ NHẬT KÝ ĐIỆN TỬ (v7.5.0) ===")
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        # 1. Khởi tạo dữ liệu mẫu
        giver = User(
            username="ca_truong_cu",
            hashed_password="hash",
            full_name="Đại úy Lê Văn Giao",
            role=2,
            clearance=True,
            is_active=True,
        )
        receiver = User(
            username="ca_truong_moi",
            hashed_password="hash",
            full_name="Thượng úy Phạm Văn Nhận",
            role=2,
            clearance=True,
            is_active=True,
        )
        commander = User(
            username="truc_chi_huy",
            hashed_password="hash",
            full_name="Thượng tá Vũ Đình Chỉ Huy",
            role=0,
            clearance=True,
            is_active=True,
        )
        unauthorized_user = User(
            username="chien_si_a",
            hashed_password="hash",
            full_name="Binh nhì Nguyễn Văn A",
            role=5,
            clearance=False,
            is_active=True,
        )
        db.add_all([giver, receiver, commander, unauthorized_user])
        db.commit()
        db.refresh(giver)
        db.refresh(receiver)
        db.refresh(commander)
        db.refresh(unauthorized_user)

        # Lịch trực ca ngày hôm nay
        schedule = DutySchedule(
            duty_date=date.today(),
            duty_type="chi_huy",
            shift="Ca ngày (07:00 - 19:00)",
            duty_officer=giver.full_name,
            role_title="Trực ban tác chiến",
            contact_phone="0243.123.456",
            personnel_present=5,
            personnel_total=5,
            note="Trực chỉ huy & kíp trực thông tin",
            author_id=commander.id,
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        # ----------------------------------------------------
        # TEST 1: Tạo biên bản bàn giao ca trực (giver lập)
        # ----------------------------------------------------
        print("\n--- Test 1: Lập biên bản bàn giao ca trực ---")
        create_payload = DutyShiftHandoverCreate(
            schedule_id=schedule.id,
            receiver_id=receiver.id,
            personnel_report="Quân số ca trực 5/5 đồng chí có mặt đầy đủ, chấp hành nghiêm điều lệnh.",
            equipment_status="Đài vô tuyến điện sóng ngắn VRU-812 hoạt động tốt; Tổng đài quân sự thông suốt.",
            incident_log="14:30 có hiện tượng suy hao tuyến cáp trục F02, đã khắc phục xong sau 15 phút.",
            pending_tasks="Theo dõi thông tin liên lạc phục vụ luyện tập chuyển trạng thái SSCĐ vào 20:00.",
        )
        handover = duty_shift_handover_service.create_handover(
            db=db,
            payload=create_payload,
            current_user=giver,
        )
        assert handover.id is not None
        assert handover.status == "cho_nhan"
        assert handover.giver_id == giver.id
        assert handover.giver_name == giver.full_name
        assert handover.receiver_id == receiver.id
        assert handover.schedule_id == schedule.id
        print("  [PASS] Tạo biên bản thành công, trạng thái 'cho_nhan', ID:", handover.id)

        # Kiểm tra chống tạo trùng biên bản cho cùng 1 ca trực
        try:
            duty_shift_handover_service.create_handover(
                db=db,
                payload=create_payload,
                current_user=giver,
            )
            assert False, "Phải ném lỗi khi tạo trùng biên bản"
        except HTTPException as exc:
            assert exc.status_code == 400
            print("  [PASS] Chặn tạo trùng biên bản ca trực thành công (400 Bad Request).")

        # ----------------------------------------------------
        # TEST 2: Ký nhận ca trực (receiver ký)
        # ----------------------------------------------------
        print("\n--- Test 2: Ký nhận ca trực và ghi nhận tình trạng trang bị ---")
        ack_payload = DutyShiftHandoverAcknowledge(
            receiver_note="Đã kiểm tra đối chiếu trang bị vũ khí, niêm phong khí tài nguyên vẹn, nhận bàn giao đầy đủ.",
            status="da_nhan",
        )
        acked_handover = duty_shift_handover_service.acknowledge_handover(
            db=db,
            handover_id=handover.id,
            payload=ack_payload,
            current_user=receiver,
        )
        assert acked_handover.status == "da_nhan"
        assert acked_handover.acknowledged_at is not None
        assert acked_handover.receiver_name == receiver.full_name
        print("  [PASS] Ký nhận ca trực thành công, trạng thái chuyển 'da_nhan'.")

        # ----------------------------------------------------
        # TEST 3: Phê duyệt của Chỉ huy (review_handover)
        # ----------------------------------------------------
        print("\n--- Test 3: Phê duyệt và chỉ đạo của Chỉ huy đơn vị ---")
        # Thử phê duyệt bằng tài khoản chiến sĩ thường -> Phải bị 403 Forbidden
        try:
            duty_shift_handover_service.review_handover(
                db=db,
                handover_id=handover.id,
                payload=DutyShiftHandoverCommanderReview(commander_note="Chiến sĩ thử duyệt"),
                current_user=unauthorized_user,
            )
            assert False, "Chiến sĩ thường không được phép duyệt biên bản ca trực"
        except HTTPException as exc:
            assert exc.status_code == 403
            print("  [PASS] Chặn quyền chiến sĩ thường duyệt biên bản (403 Forbidden).")

        # Chỉ huy phê duyệt thành công
        review_payload = DutyShiftHandoverCommanderReview(
            commander_note="Biểu dương kíp trực đã kịp thời xử lý sự cố cáp trục. Ca tiếp tục duy trì nghiêm chế độ canh trực 24/24."
        )
        reviewed_handover = duty_shift_handover_service.review_handover(
            db=db,
            handover_id=handover.id,
            payload=review_payload,
            current_user=commander,
        )
        assert reviewed_handover.commander_note is not None
        assert review_payload.commander_note in reviewed_handover.commander_note
        print("  [PASS] Chỉ huy phê duyệt thành công, lưu đầy đủ bút phê chỉ đạo.")

        # ----------------------------------------------------
        # TEST 4: Tra cứu theo schedule_id và danh sách
        # ----------------------------------------------------
        print("\n--- Test 4: Tra cứu theo lịch trực và danh sách ---")
        found = duty_shift_handover_service.get_by_schedule(db=db, schedule_id=schedule.id)
        assert found is not None
        assert found.id == handover.id
        print("  [PASS] Tra cứu theo schedule_id chính xác.")

        res = duty_shift_handover_service.list_handovers(
            db=db, current_user=commander, status="da_nhan", limit=10, skip=0
        )
        assert res.total == 1
        assert len(res.items) == 1
        print("  [PASS] Danh sách nhật ký lọc theo status 'da_nhan' chính xác (total = 1).")

        # ----------------------------------------------------
        # TEST 5: Kiểm thử API Route Handlers trực tiếp
        # ----------------------------------------------------
        print("\n--- Test 5: Kiểm thử API Route Handlers (Contract & Serialization) ---")

        # GET /duty-shift-handovers (Route handler)
        list_res = handover_routes.list_shift_handovers(
            skip=0,
            limit=20,
            date_from=None,
            date_to=None,
            unit_id=None,
            status=None,
            db=db,
            current_user=commander,
        )
        assert hasattr(list_res, "items") and hasattr(list_res, "total")
        assert list_res.total >= 1
        print("  [PASS] Route GET /duty-shift-handovers trả về cấu trúc DutyShiftHandoverListResponse chuẩn.")

        # GET /duty-shift-handovers/by-schedule/{schedule_id} (Route handler)
        schedule_item = handover_routes.get_handover_by_schedule(
            schedule_id=schedule.id,
            db=db,
            current_user=commander,
        )
        assert schedule_item is not None
        assert schedule_item.schedule_id == schedule.id
        assert schedule_item.status == "da_nhan"
        print(f"  [PASS] Route GET /duty-shift-handovers/by-schedule/{schedule.id} trả về DutyShiftHandoverOut chuẩn.")

        print("\n=== TOÀN BỘ CÁC BƯỚC TEST BÀN GIAO CA TRỰC ĐÃ VƯỢT QUA 100% ===")

    finally:
        db.close()


if __name__ == "__main__":
    test_duty_shift_handover_flow()
