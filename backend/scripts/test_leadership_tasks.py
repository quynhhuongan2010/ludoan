"""
Script kiểm thử tự động tính năng Bàn làm việc Chỉ đạo Ban Chỉ huy Lữ đoàn (Step 7 - v7.7.0).
Bao gồm:
1. Ban Chỉ huy Lữ đoàn (role <= 2) ban hành Chỉ đạo / Mệnh lệnh (create_task)
2. Kiểm tra chặn quyền: Chiến sĩ / người dùng thường (role 3) không được ban hành chỉ đạo (HTTP 403)
3. Đơn vị cơ sở / Trợ lý báo cáo tiến độ, kết quả thực hiện (submit_report)
4. Ban Chỉ huy đánh giá kết quả, bút phê chỉ đạo hoàn thành (review_task)
5. Kiểm tra chặn quyền: Chiến sĩ không được bút phê duyệt nhiệm vụ chỉ đạo (HTTP 403)
6. Lọc và tìm kiếm theo chức danh (lu_truong, chinh_uy, lu_pho_tmt...), khối ngành, độ khẩn, trạng thái
7. Kiểm tra hệ thống Audit Log ghi nhận đầy đủ các vết an ninh quân sự
8. Kiểm thử API Route Handlers (Contract & Serialization)
"""

import sys
from pathlib import Path
from datetime import datetime, date

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.models.user import User
from app.models.unit import Unit
from app.models.leadership_task import LeadershipTask
from app.models.audit_log import AuditLog
from app.schemas.leadership_task import (
    LeadershipTaskCreate,
    LeadershipTaskReport,
    LeadershipTaskReview,
)
from app.services import leadership_task_service
from app.api.routes import leadership_tasks as task_routes


def test_leadership_tasks_full_flow():
    print("=== BẮT ĐẦU KIỂM THỬ BÀN LÀM VIỆC CHỈ ĐẠO BAN CHỈ HUY LỮ ĐOÀN (v7.7.0) ===")
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        # 1. Khởi tạo đơn vị và người dùng
        unit_tm = Unit(id=1, name="Phòng Tham mưu", unit_kind="phong_ban")
        unit_d1 = Unit(id=2, name="Tiểu đoàn 1", unit_kind="tieu_doan")
        db.add_all([unit_tm, unit_d1])
        db.commit()

        lu_truong = User(
            id=1,
            username="lu_truong_21",
            hashed_password="hash",
            full_name="Đại tá Nguyễn Văn An",
            role=1,
            clearance=True,
            is_active=True,
            unit_id=1,
        )
        chinh_uy = User(
            id=2,
            username="chinh_uy_21",
            hashed_password="hash",
            full_name="Đại tá Trần Quang Minh",
            role=1,
            clearance=True,
            is_active=True,
            unit_id=1,
        )
        tro_ly_d1 = User(
            id=3,
            username="tro_ly_d1",
            hashed_password="hash",
            full_name="Đại úy Hoàng Đức Thắng",
            role=3,
            clearance=True,
            is_active=True,
            unit_id=2,
        )
        db.add_all([lu_truong, chinh_uy, tro_ly_d1])
        db.commit()

        # ----------------------------------------------------------------------
        # TEST CASE 1: Lữ trưởng ban hành Chỉ đạo tác chiến SSCĐ
        # ----------------------------------------------------------------------
        print("\n--- Test 1: Lữ trưởng ban hành chỉ đạo tác chiến SSCĐ ---")
        task_payload = LeadershipTaskCreate(
            commander_role="lu_truong",
            title="Duy trì nghiêm chế độ trực chỉ huy, trực SSCĐ cao điểm Lễ",
            content="Yêu cầu d1, d2 và các trạm TTLL kiểm tra 100% phương tiện thông tin cơ động, không để gián đoạn liên lạc.",
            target_branch="tham_muu",
            assigned_unit_id=2,
            urgency="hoa_toc",
            deadline=date(2026, 9, 10),
        )
        created_task = leadership_task_service.create_task(db=db, current_user=lu_truong, payload=task_payload)
        assert created_task.id is not None
        assert created_task.commander_role == "lu_truong"
        assert created_task.commander_name == "Đại tá Nguyễn Văn An"
        assert created_task.urgency == "hoa_toc"
        assert created_task.status == "dang_thuc_hien"
        assert created_task.assigned_unit_name == "Tiểu đoàn 1"
        print(f"-> Ban hành thành công chỉ đạo ID={created_task.id} với độ khẩn='{created_task.urgency_label}'")

        # ----------------------------------------------------------------------
        # TEST CASE 2: Chặn quyền - Người dùng role=3 không được tạo chỉ đạo
        # ----------------------------------------------------------------------
        print("\n--- Test 2: Chặn quyền chiến sĩ/trợ lý role=3 không được tạo chỉ đạo ---")
        unauthorized_blocked = False
        try:
            leadership_task_service.create_task(db=db, current_user=tro_ly_d1, payload=task_payload)
        except HTTPException as e:
            if e.status_code == 403:
                unauthorized_blocked = True
                print(f"-> Đã chặn thành công: {e.detail}")
        assert unauthorized_blocked, "Lỗi: Người dùng role=3 không được phép ban hành chỉ đạo!"

        # ----------------------------------------------------------------------
        # TEST CASE 3: Đơn vị cơ sở (d1) báo cáo kết quả thực hiện
        # ----------------------------------------------------------------------
        print("\n--- Test 3: Đơn vị d1 báo cáo kết quả thực hiện chỉ đạo ---")
        report_payload = LeadershipTaskReport(
            report_content="Tiểu đoàn 1 đã kiểm tra xong 100% trang bị khí tài xe TT cơ động, bảo đảm thông suốt 24/24."
        )
        reported_task = leadership_task_service.submit_report(
            db=db, current_user=tro_ly_d1, task_id=created_task.id, payload=report_payload
        )
        assert reported_task.report_content == report_payload.report_content
        assert reported_task.reported_by_name == "Đại úy Hoàng Đức Thắng"
        assert reported_task.reported_at is not None
        assert reported_task.status == "da_bao_cao", f"Nộp báo cáo phải chuyển trạng thái 'da_bao_cao', đang là '{reported_task.status}'"
        print(f"-> Báo cáo thành công lúc {reported_task.reported_at} (trạng thái -> '{reported_task.status_label}')")

        # ----------------------------------------------------------------------
        # TEST CASE 4: Chặn quyền - Chiến sĩ/trợ lý role=3 không được duyệt bút phê
        # ----------------------------------------------------------------------
        print("\n--- Test 4: Chặn quyền chiến sĩ/trợ lý role=3 không được bút phê duyệt ---")
        review_blocked = False
        review_payload = LeadershipTaskReview(
            status="da_hoan_thanh",
            review_note="Biểu dương d1 hoàn thành tốt nhiệm vụ, tiếp tục duy trì nghiêm ngặt.",
        )
        try:
            leadership_task_service.review_task(
                db=db, current_user=tro_ly_d1, task_id=created_task.id, payload=review_payload
            )
        except HTTPException as e:
            if e.status_code == 403:
                review_blocked = True
                print(f"-> Đã chặn thành công: {e.detail}")
        assert review_blocked, "Lỗi: Người dùng role=3 không được phép duyệt chỉ đạo!"

        # ----------------------------------------------------------------------
        # TEST CASE 5: Lữ trưởng đánh giá kết quả & bút phê hoàn thành
        # ----------------------------------------------------------------------
        print("\n--- Test 5: Lữ trưởng đánh giá kết quả và bút phê hoàn thành ---")
        reviewed_task = leadership_task_service.review_task(
            db=db, current_user=lu_truong, task_id=created_task.id, payload=review_payload
        )
        assert reviewed_task.status == "da_hoan_thanh"
        assert reviewed_task.review_note == review_payload.review_note
        assert reviewed_task.reviewed_at is not None
        print(f"-> Đã bút phê thành công: trạng thái='{reviewed_task.status_label}', nhận xét='{reviewed_task.review_note}'")

        # ----------------------------------------------------------------------
        # TEST CASE 6: Danh sách & Bộ lọc chỉ đạo (Commander Role, Branch, Urgency)
        # ----------------------------------------------------------------------
        print("\n--- Test 6: Kiểm tra bộ lọc chỉ đạo nghiệp vụ ---")
        # Thêm 1 chỉ đạo từ Chính uỷ
        cu_payload = LeadershipTaskCreate(
            commander_role="chinh_uy",
            title="Đợt sinh hoạt chính trị tư tưởng quý III/2026",
            content="Tổ chức quán triệt tinh thần SSCĐ và rèn luyện kỷ luật cho toàn thể cán bộ chiến sĩ.",
            target_branch="chinh_tri",
            assigned_unit_id=None,
            urgency="thuong",
        )
        leadership_task_service.create_task(db=db, current_user=chinh_uy, payload=cu_payload)

        # Lọc theo role lu_truong (Lữ trưởng là Ban Chỉ huy -> thấy mọi chỉ đạo)
        res_lt = leadership_task_service.list_tasks(db=db, current_user=lu_truong, commander_role="lu_truong")
        assert res_lt.total == 1
        assert res_lt.items[0].commander_role == "lu_truong"
        print(f"-> Lọc theo Lữ trưởng: tìm thấy {res_lt.total} chỉ đạo (chính xác)")

        # Lọc theo branch chinh_tri
        res_ct = leadership_task_service.list_tasks(db=db, current_user=lu_truong, target_branch="chinh_tri")
        assert res_ct.total == 1
        assert res_ct.items[0].target_branch == "chinh_tri"
        print(f"-> Lọc theo Khối Chính trị: tìm thấy {res_ct.total} chỉ đạo (chính xác)")

        # Lọc tất cả
        res_all = leadership_task_service.list_tasks(db=db, current_user=lu_truong)
        assert res_all.total == 2
        print(f"-> Tổng số chỉ đạo toàn Lữ đoàn: {res_all.total}")

        # ----------------------------------------------------------------------
        # TEST CASE 7: Kiểm tra Audit Log an ninh quân sự
        # ----------------------------------------------------------------------
        print("\n--- Test 7: Kiểm tra nhật ký an ninh audit_logs ---")
        logs = db.query(AuditLog).filter(AuditLog.target_type == "leadership_task").all()
        actions = [log.action for log in logs]
        print(f"-> Các hành động ghi nhận trong audit_logs: {actions}")
        assert "LEADERSHIP_TASK_CREATED" in actions
        assert "LEADERSHIP_TASK_REPORTED" in actions
        assert "LEADERSHIP_TASK_REVIEWED" in actions

        # ----------------------------------------------------------------------
        # TEST CASE 8: Kiểm thử API Route Handlers (Contract & Serialization)
        # ----------------------------------------------------------------------
        print("\n--- Test 8: Kiểm thử API Route Handlers (Contract & Serialization) ---")

        # GET /leadership-tasks
        list_resp = task_routes.list_leadership_tasks(
            skip=0,
            limit=10,
            commander_role=None,
            target_branch=None,
            assigned_unit_id=None,
            status=None,
            urgency=None,
            db=db,
            current_user=lu_truong,
        )
        assert hasattr(list_resp, "items") and hasattr(list_resp, "total")
        assert list_resp.total == 2
        print(f"-> Route GET /leadership-tasks trả về LeadershipTaskListResponse chuẩn (total={list_resp.total})")

        # GET /leadership-tasks/{id}
        detail_resp = task_routes.get_leadership_task(
            id=created_task.id,
            db=db,
            current_user=lu_truong,
        )
        assert detail_resp.id == created_task.id
        assert detail_resp.commander_role == "lu_truong"
        print(f"-> Route GET /leadership-tasks/{created_task.id} trả về LeadershipTaskOut chuẩn")

        # POST /leadership-tasks
        post_payload = LeadershipTaskCreate(
            commander_role="lu_pho_tmt",
            title="Kiểm tra phiên liên lạc mạng vô tuyến điện sóng ngắn",
            content="Tiến hành phiên liên lạc đặc biệt lúc 14h00 với Sở chỉ huy Binh chủng.",
            target_branch="tham_muu",
            urgency="khan",
        )
        post_created = task_routes.create_leadership_task(
            payload=post_payload,
            db=db,
            current_user=lu_truong,
        )
        assert post_created.id is not None
        assert post_created.commander_role == "lu_pho_tmt"
        print(f"-> Route POST /leadership-tasks trả về LeadershipTaskOut chuẩn (ID={post_created.id})")

        print("\n=== TOÀN BỘ KIỂM THỬ BÀN LÀM VIỆC BAN CHỈ HUY (v7.7.0) THÀNH CÔNG 100%! ===")

    finally:
        db.close()


if __name__ == "__main__":
    test_leadership_tasks_full_flow()
