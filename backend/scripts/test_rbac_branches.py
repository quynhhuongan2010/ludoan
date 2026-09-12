"""
Script test tự động tính năng Phân quyền đa cấp theo Khối/Ngành (Step 6 - v7.6.0)
1. Kiểm tra xác định Khối/Ngành quân sự (get_user_branch)
2. Kiểm tra phân định thẩm quyền chuyên trách giữa các Khối (can_manage_branch, can_manage_political_education, can_manage_technical_equipment)
3. Kiểm tra toàn quyền của Ban Chỉ huy Lữ đoàn & Quản trị hệ thống
4. Kiểm tra ma trận quyền hạn (get_permission_matrix)
5. Kiểm thử API endpoint GET /profile/permissions
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User
from app.models.unit import Unit
from app.core import rbac
from app.api.routes import profile as profile_routes


def test_rbac_flow():
    print("=== BẮT ĐẦU KIỂM THỬ PHÂN QUYỀN ĐA CẤP THEO KHỐI/NGÀNH (v7.6.0) ===")
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        # 1. Tạo các đơn vị theo cơ cấu tổ chức chuẩn
        u_bch = Unit(name="Ban chỉ huy Lữ đoàn", unit_kind="bch_lu_doan", is_active=True)
        u_tm = Unit(name="Phòng Tham mưu", unit_kind="phong_ban", is_active=True)
        u_ct = Unit(name="Phòng Chính trị", unit_kind="phong_ban", is_active=True)
        u_hc_kt = Unit(name="Phòng Hậu cần – Kỹ thuật", unit_kind="phong_ban", is_active=True)
        u_d1 = Unit(name="Tiểu đoàn 1", unit_kind="tieu_doan", is_active=True)

        db.add_all([u_bch, u_tm, u_ct, u_hc_kt, u_d1])
        db.commit()
        for u in (u_bch, u_tm, u_ct, u_hc_kt, u_d1):
            db.refresh(u)

        # 2. Tạo các quân nhân với vai trò và đơn vị tương ứng
        commander = User(
            username="lu_truong",
            hashed_password="hash",
            full_name="Đại tá Hoàng Văn Lữ Trưởng",
            role=1,
            unit_id=u_bch.id,
            clearance=True,
            is_active=True,
        )
        commander.unit = u_bch

        officer_tm = User(
            username="tro_ly_tac_chien",
            hashed_password="hash",
            full_name="Thiếu tá Trần Văn Tác Chiến",
            role=4,
            unit_id=u_tm.id,
            clearance=True,
            is_active=True,
        )
        officer_tm.unit = u_tm

        officer_ct = User(
            username="tro_ly_tuyen_huan",
            hashed_password="hash",
            full_name="Đại úy Lê Văn Tuyên Huấn",
            role=4,
            unit_id=u_ct.id,
            clearance=False,
            is_active=True,
        )
        officer_ct.unit = u_ct

        officer_hc_kt = User(
            username="tro_ly_khi_tai",
            hashed_password="hash",
            full_name="Trung tá Phạm Văn Khí Tài",
            role=4,
            unit_id=u_hc_kt.id,
            clearance=False,
            is_active=True,
        )
        officer_hc_kt.unit = u_hc_kt

        soldier = User(
            username="chien_si_d1",
            hashed_password="hash",
            full_name="Binh nhất Nguyễn Văn Bình",
            role=5,
            unit_id=u_d1.id,
            clearance=False,
            is_active=True,
        )
        soldier.unit = u_d1

        db.add_all([commander, officer_tm, officer_ct, officer_hc_kt, soldier])
        db.commit()
        for u in (commander, officer_tm, officer_ct, officer_hc_kt, soldier):
            db.refresh(u)

        # ----------------------------------------------------
        # TEST 1: Xác định Khối/Ngành quân sự (get_user_branch)
        # ----------------------------------------------------
        print("\n--- Test 1: Xác định Khối/Ngành cơ quan tự động ---")
        assert rbac.get_user_branch(commander) == rbac.BRANCH_TOAN_LU_DOAN
        assert rbac.get_user_branch(officer_tm) == rbac.BRANCH_THAM_MUU
        assert rbac.get_user_branch(officer_ct) == rbac.BRANCH_CHINH_TRI
        assert rbac.get_user_branch(officer_hc_kt) == rbac.BRANCH_HAU_CAN_KY_THUAT
        assert rbac.get_user_branch(soldier) == rbac.BRANCH_DON_VI_CO_SO
        print("  [PASS] Xác định đúng 100% Khối/Ngành cho toàn bộ 5 nhóm tài khoản.")

        # ----------------------------------------------------
        # TEST 2: Phân định thẩm quyền chuyên trách giữa các Khối
        # ----------------------------------------------------
        print("\n--- Test 2: Phân định thẩm quyền chuyên trách theo ngành ---")
        # Khối Tham mưu
        assert rbac.can_manage_branch(officer_tm, rbac.BRANCH_THAM_MUU) is True
        assert rbac.can_manage_branch(officer_tm, rbac.BRANCH_CHINH_TRI) is False
        assert rbac.can_manage_branch(officer_tm, rbac.BRANCH_HAU_CAN_KY_THUAT) is False
        print("  [PASS] Cán bộ Tham mưu quản lý đúng khối Tham mưu, không can thiệp Chính trị / Hậu cần-KT.")

        # Khối Chính trị
        assert rbac.can_manage_political_education(officer_ct) is True
        assert rbac.can_manage_technical_equipment(officer_ct) is False
        assert rbac.can_manage_branch(officer_ct, rbac.BRANCH_THAM_MUU) is False
        print("  [PASS] Cán bộ Chính trị quản lý đúng Tư liệu Giáo dục chính trị & Tuyên huấn.")

        # Khối Hậu cần – Kỹ thuật
        assert rbac.can_manage_technical_equipment(officer_hc_kt) is True
        assert rbac.can_manage_political_education(officer_hc_kt) is False
        assert rbac.can_manage_branch(officer_hc_kt, rbac.BRANCH_THAM_MUU) is False
        print("  [PASS] Cán bộ Hậu cần – Kỹ thuật quản lý đúng Khí tài & Trang bị VKTB.")

        # ----------------------------------------------------
        # TEST 3: Toàn quyền của Ban Chỉ huy Lữ đoàn
        # ----------------------------------------------------
        print("\n--- Test 3: Toàn quyền chỉ đạo của Chỉ huy Lữ đoàn ---")
        assert rbac.can_manage_branch(commander, rbac.BRANCH_THAM_MUU) is True
        assert rbac.can_manage_branch(commander, rbac.BRANCH_CHINH_TRI) is True
        assert rbac.can_manage_branch(commander, rbac.BRANCH_HAU_CAN_KY_THUAT) is True
        assert rbac.can_manage_political_education(commander) is True
        assert rbac.can_manage_technical_equipment(commander) is True
        assert rbac.can_review_duty(commander) is True
        print("  [PASS] Chỉ huy Lữ đoàn có thẩm quyền toàn diện trên mọi khối ngành quân sự.")

        # Người dùng thường / Chiến sĩ cơ sở không có quyền quản lý
        assert rbac.can_manage_branch(soldier, rbac.BRANCH_THAM_MUU) is False
        assert rbac.can_manage_political_education(soldier) is False
        assert rbac.can_manage_technical_equipment(soldier) is False
        print("  [PASS] Chiến sĩ cơ sở (role 5) bị chặn các quyền quản trị khối ngành.")

        # ----------------------------------------------------
        # TEST 4: Xuất Ma trận quyền hạn (get_permission_matrix)
        # ----------------------------------------------------
        print("\n--- Test 4: Xuất ma trận quyền hạn (RBAC Matrix) ---")
        matrix_tm = rbac.get_permission_matrix(officer_tm)
        assert matrix_tm["branch"] == rbac.BRANCH_THAM_MUU
        assert matrix_tm["permissions"]["manage_tham_muu"] is True
        assert matrix_tm["permissions"]["manage_chinh_tri"] is False
        assert matrix_tm["permissions"]["manage_hau_can_ky_thuat"] is False
        assert matrix_tm["permissions"]["publish_news"] is True
        print("  [PASS] Ma trận quyền hạn cán bộ Tham mưu chính xác.")

        matrix_cmd = rbac.get_permission_matrix(commander)
        assert matrix_cmd["branch"] == rbac.BRANCH_TOAN_LU_DOAN
        assert matrix_cmd["permissions"]["is_commander"] is True
        assert matrix_cmd["permissions"]["view_audit_logs"] is True
        assert matrix_cmd["permissions"]["manage_users"] is True
        print("  [PASS] Ma trận quyền hạn Chỉ huy Lữ đoàn chính xác.")

        # ----------------------------------------------------
        # TEST 5: API Endpoint GET /profile/permissions
        # ----------------------------------------------------
        print("\n--- Test 5: Kiểm thử Route Handler GET /profile/permissions ---")
        res = profile_routes.get_my_permissions(current_user=officer_ct)
        assert res.username == officer_ct.username
        assert res.branch == rbac.BRANCH_CHINH_TRI
        assert res.branch_label == rbac.BRANCH_LABELS[rbac.BRANCH_CHINH_TRI]
        assert res.permissions["manage_chinh_tri"] is True
        assert res.permissions["manage_tham_muu"] is False
        assert res.unit_name == "Phòng Chính trị"
        print("  [PASS] Endpoint GET /profile/permissions trả về UserPermissionsOut chuẩn.")

        print("\n=== TOÀN BỘ KIỂM THỬ PHÂN QUYỀN ĐA CẤP KHỐI/NGÀNH ĐÃ ĐẠT 100%! ===")

    finally:
        db.close()


if __name__ == "__main__":
    test_rbac_flow()
