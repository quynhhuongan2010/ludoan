"""Khoi tao danh sach 18 tai khoan mau chuan bien che Lu doan Thong tin 21.

Idempotent - neu tai khoan da ton tai thi cap nhat lai thong tin dong bo,
neu chua co thi tao moi.
Chay:
    venv/Scripts/python.exe scripts/seed_military_accounts.py
"""

import pathlib
import sys

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.bootstrap import ensure_standard_units
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.unit import Unit
from app.models.user import User

DEFAULT_PASSWORD = "LuDoan21@2026"

MILITARY_ACCOUNTS = [
    # 1. Ban Chi huy Lu doan
    {
        "username": "lu_truong",
        "full_name": "Nguyễn Văn Thắng",
        "rank": "Đại tá",
        "position": "Lữ đoàn trưởng (Chỉ đạo chung chính quyền)",
        "unit_name": "Ban chỉ huy Lữ đoàn",
        "role": 1,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": True,
    },
    {
        "username": "chinh_uy",
        "full_name": "Trần Văn Nam",
        "rank": "Đại tá",
        "position": "Chính uỷ Lữ đoàn (Chỉ đạo công tác Đảng, CTĐ-CTCT)",
        "unit_name": "Ban chỉ huy Lữ đoàn",
        "role": 1,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": True,
    },
    {
        "username": "lu_pho_tm",
        "full_name": "Lê Văn Hải",
        "rank": "Thượng tá",
        "position": "Phó Lữ đoàn trưởng kiêm Tham mưu trưởng",
        "unit_name": "Ban chỉ huy Lữ đoàn",
        "role": 2,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": True,
    },
    {
        "username": "lu_pho_hckt",
        "full_name": "Hoàng Đức Long",
        "rank": "Thượng tá",
        "position": "Phó Lữ đoàn trưởng (Chỉ đạo Hậu cần - Kỹ thuật)",
        "unit_name": "Ban chỉ huy Lữ đoàn",
        "role": 2,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": True,
    },
    {
        "username": "pho_chinh_uy",
        "full_name": "Phạm Văn Hùng",
        "rank": "Thượng tá",
        "position": "Phó Chính uỷ (Chỉ đạo các tổ chức quần chúng)",
        "unit_name": "Ban chỉ huy Lữ đoàn",
        "role": 2,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": True,
    },

    # 2. Phong ban chuc nang
    {
        "username": "tm_truong",
        "full_name": "Đỗ Văn Cường",
        "rank": "Trung tá",
        "position": "Trưởng phòng Tham mưu",
        "unit_name": "Phòng Tham mưu",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "tro_ly_tac_chien",
        "full_name": "Vũ Tuấn Anh",
        "rank": "Thiếu tá",
        "position": "Trợ lý Tác chiến - Thông tin liên lạc",
        "unit_name": "Phòng Tham mưu",
        "role": 4,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "ct_truong",
        "full_name": "Nguyễn Hoàng Nam",
        "rank": "Trung tá",
        "position": "Chủ nhiệm Chính trị",
        "unit_name": "Phòng Chính trị",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "tro_ly_tuyen_huan",
        "full_name": "Lê Hồng Phúc",
        "rank": "Đại uý",
        "position": "Trợ lý Tuyên huấn - CTĐ-CTCT",
        "unit_name": "Phòng Chính trị",
        "role": 4,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "hckt_truong",
        "full_name": "Bùi Văn Toàn",
        "rank": "Trung tá",
        "position": "Chủ nhiệm Hậu cần – Kỹ thuật",
        "unit_name": "Phòng Hậu cần – Kỹ thuật",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "tro_ly_quan_khi",
        "full_name": "Trần Đình Trọng",
        "rank": "Đại uý",
        "position": "Trợ lý Quân khí - Xe máy TTLL",
        "unit_name": "Phòng Hậu cần – Kỹ thuật",
        "role": 4,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },

    # 3. Cac don vi co so truc thuoc
    {
        "username": "d1_truong",
        "full_name": "Hoàng Văn Dũng",
        "rank": "Thiếu tá",
        "position": "Tiểu đoàn trưởng Tiểu đoàn 1",
        "unit_name": "Tiểu đoàn 1",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "d1_chinh_tri_vien",
        "full_name": "Trịnh Xuân Hưng",
        "rank": "Thiếu tá",
        "position": "Chính trị viên Tiểu đoàn 1",
        "unit_name": "Tiểu đoàn 1",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "d2_truong",
        "full_name": "Ngô Văn Hùng",
        "rank": "Thiếu tá",
        "position": "Tiểu đoàn trưởng Tiểu đoàn 2",
        "unit_name": "Tiểu đoàn 2",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "c5_truong",
        "full_name": "Vũ Đình Phong",
        "rank": "Đại uý",
        "position": "Đại đội trưởng Đại đội 5 (Trực thuộc)",
        "unit_name": "Đại đội 5",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "tt2_truong",
        "full_name": "Nguyễn Trọng Tấn",
        "rank": "Thiếu tá",
        "position": "Giám đốc Trung tâm 2",
        "unit_name": "Trung tâm 2",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "tram_kiem_soat",
        "full_name": "Đặng Thành Vinh",
        "rank": "Đại uý",
        "position": "Trạm trưởng Trạm Kiểm soát TTLL",
        "unit_name": "Trạm Kiểm soát",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
    {
        "username": "tram_bao_dam",
        "full_name": "Phan Văn Khánh",
        "rank": "Đại uý",
        "position": "Trạm trưởng Trạm bảo đảm kỹ thuật TTLL",
        "unit_name": "Trạm bảo đảm",
        "role": 3,
        "clearance": True,
        "directive_channel_access": True,
        "command_channel_access": False,
    },
]


def seed_military_accounts():
    with SessionLocal() as db:
        ensure_standard_units(db)
        unit_map = {u.name: u.id for u in db.query(Unit).all()}

        created_count = 0
        updated_count = 0

        for acc in MILITARY_ACCOUNTS:
            unit_id = unit_map.get(acc["unit_name"])
            existing_user = db.query(User).filter(User.username == acc["username"]).first()

            if existing_user:
                existing_user.full_name = acc["full_name"]
                existing_user.rank = acc["rank"]
                existing_user.position = acc["position"]
                existing_user.unit_id = unit_id
                existing_user.role = acc["role"]
                existing_user.is_active = True
                existing_user.clearance = acc["clearance"]
                existing_user.directive_channel_access = acc["directive_channel_access"]
                existing_user.command_channel_access = acc["command_channel_access"]
                existing_user.hashed_password = hash_password(DEFAULT_PASSWORD)
                existing_user.must_change_password = False
                updated_count += 1
            else:
                new_u = User(
                    username=acc["username"],
                    full_name=acc["full_name"],
                    rank=acc["rank"],
                    position=acc["position"],
                    unit_id=unit_id,
                    role=acc["role"],
                    is_active=True,
                    clearance=acc["clearance"],
                    directive_channel_access=acc["directive_channel_access"],
                    command_channel_access=acc["command_channel_access"],
                    hashed_password=hash_password(DEFAULT_PASSWORD),
                    must_change_password=False,
                )
                db.add(new_u)
                created_count += 1

        db.commit()

        print(f"=== ĐÃ KHỞI TẠO BỘ TÀI KHOẢN CHUẨN BIÊN CHẾ LỮ ĐOÀN 21 ===")
        print(f"+ Tạo mới: {created_count} tài khoản")
        print(f"+ Cập nhật: {updated_count} tài khoản")
        print(f"+ Mật khẩu mặc định: {DEFAULT_PASSWORD}")
        print(f"+ Tổng số tài khoản: {len(MILITARY_ACCOUNTS)}")


if __name__ == "__main__":
    seed_military_accounts()
