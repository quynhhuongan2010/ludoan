"""Khoi tao tai khoan admin he thong.

Chay khi ung dung khoi dong (goi trong `app/main.py`) hoac chay tay bang
`scripts/seed_admin.py`. Doc `SYSTEM_ADMIN_USERNAME` / `SYSTEM_ADMIN_PASSWORD`
tu `.env` (co gia tri mac dinh `admin` / `admin`).

Quy tac:
  - Neu da co bat ky tai khoan nao `is_system = True` -> khong lam gi.
  - Neu username trung voi tai khoan da ton tai -> nang cap tai khoan do
    (`is_system = True`, `role = 0` [Quản trị hệ thống], `is_active = True`).
  - Nguoc lai -> tao moi tai khoan admin he thong, `must_change_password = True`.
"""

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.roles import ROLE_ADMIN
from app.core.security import hash_password
from app.models.unit import Unit
from app.models.user import User
from app.repositories import user_repository

logger = logging.getLogger(__name__)

# Co cau to chuc chuan Lu doan Thong tin 21: (ten, unit_kind, mo ta)
STANDARD_UNITS = [
    ("Ban chỉ huy Lữ đoàn", "bch_lu_doan", "Lữ trưởng (Chính quyền), Chính uỷ (Đảng), các Lữ phó chuyên ngành, Phó Chính uỷ (Quần chúng)"),
    ("Cấp uỷ – Đảng bộ Lữ đoàn", "cap_uy", "Cấp uỷ, Đảng bộ Lữ đoàn"),
    ("Phòng Tham mưu", "phong_ban",
     "Cơ quan Tham mưu — chỉ đạo chuyên ngành tác chiến, huấn luyện, SSCĐ, hệ thống TTLL"),
    ("Phòng Chính trị", "phong_ban",
     "Cơ quan Chính trị — chỉ đạo CTĐ - CTCT, cán bộ, tuyên huấn, bảo vệ an ninh"),
    ("Phòng Hậu cần – Kỹ thuật", "phong_ban",
     "Cơ quan Hậu cần – Kỹ thuật — chỉ đạo bảo đảm VKTB, khí tài TTLL, xe máy, hậu cần, quân y"),
    ("Tiểu đoàn 1", "tieu_doan", "Đầu mối Tiểu đoàn 1 — đơn vị thông tin tác chiến"),
    ("Tiểu đoàn 2", "tieu_doan", "Đầu mối Tiểu đoàn 2 — đơn vị thông tin tác chiến"),
    ("Đại đội 5", "dai_doi", "Đầu mối Đại đội 5 trực thuộc"),
    ("Trung tâm 2", "phong_ban", "Trung tâm 2 — trung tâm TTLL trọng điểm trực thuộc"),
    ("Trạm Kiểm soát", "tram", "Trạm Kiểm soát thông tin liên lạc"),
    ("Trạm bảo đảm", "tram", "Trạm bảo đảm thông tin liên lạc"),
]


def ensure_standard_units(db: Session) -> list[str]:
    """Tao cac don vi con THIEU (so khop theo ten). Idempotent, khong dung don vi da co."""
    have = {u.name for u in db.query(Unit).all()}
    added: list[str] = []
    for name, kind, desc in STANDARD_UNITS:
        if name in have:
            continue
        db.add(Unit(name=name, unit_kind=kind, description=desc, is_active=True))
        added.append(name)
    if added:
        db.commit()
        logger.info("Da khoi tao %d don vi chuan: %s", len(added), ", ".join(added))
    return added


def ensure_system_admin(db: Session) -> User | None:
    if user_repository.get_first_system(db) is not None:
        return None

    username = settings.SYSTEM_ADMIN_USERNAME
    existing = user_repository.get_by_username(db, username)
    if existing is not None:
        existing.is_system = True
        existing.role = ROLE_ADMIN
        existing.is_active = True
        db.add(existing)
        db.commit()
        db.refresh(existing)
        logger.info("Da nang cap tai khoan '%s' thanh admin he thong", username)
        return existing

    admin = User(
        username=username,
        hashed_password=hash_password(settings.SYSTEM_ADMIN_PASSWORD),
        full_name="Quản trị hệ thống",
        role=ROLE_ADMIN,
        is_active=True,
        clearance=True,
        is_system=True,
        must_change_password=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    logger.info("Da tao tai khoan admin he thong '%s' (buoc doi mat khau lan dau)", username)
    return admin
