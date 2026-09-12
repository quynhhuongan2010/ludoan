# -*- coding: utf-8 -*-
"""FACTORY RESET CSDL — xoa sach toan bo du lieu, dung lai schema rong roi tu
tao lai tai khoan admin he thong + 10 don vi chuan (giong het lan chay dau tien).

    KHONG con: user (tru admin), post, chi thi, luong trao doi, chat, cong van,
    thong bao, tai lieu, GDCT, lich truc, audit log, leadership task, contact...
    CON LAI: 1 tai khoan `admin` (mat khau theo SYSTEM_ADMIN_* trong .env) +
    10 don vi chuan.

An toan:
  - Bat buoc co co `--yes` moi chay (tranh xoa nham).
  - NEN backup truoc:  venv/Scripts/python.exe scripts/backup_db.py

Cach dung:
    venv/Scripts/python.exe scripts/factory_reset_db.py --yes

Sau khi chay xong: khoi dong lai backend (dong cua so uvicorn cu, chay lai
Chay_He_Thong.bat) de pool ket noi lam moi.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import engine  # noqa: E402


def _row_counts() -> dict[str, int]:
    insp = inspect(engine)
    out: dict[str, int] = {}
    with engine.connect() as conn:
        for t in insp.get_table_names():
            try:
                out[t] = conn.execute(text(f"SELECT COUNT(*) FROM `{t}`")).scalar() or 0
            except Exception:  # noqa: BLE001
                out[t] = -1
    return out


def _drop_all_tables() -> list[str]:
    insp = inspect(engine)
    tables = insp.get_table_names()
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for t in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS `{t}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    return tables


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yes", action="store_true", help="Xac nhan xoa sach - bat buoc")
    args = ap.parse_args()

    print(f"CSDL muc tieu : {settings.MYSQL_DATABASE} @ {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    before = _row_counts()
    non_empty = {k: v for k, v in before.items() if v}
    print(f"Bang hien co  : {len(before)}  |  Bang co du lieu: {len(non_empty)}")
    for k, v in sorted(non_empty.items()):
        print(f"    - {k:<32} {v}")

    if not args.yes:
        print("\n[DUNG LAI] Them co `--yes` de thuc su xoa sach. Nen backup truoc:")
        print("    venv/Scripts/python.exe scripts/backup_db.py")
        sys.exit(1)

    print("\n>> Dang DROP toan bo bang...")
    dropped = _drop_all_tables()
    print(f"   Da drop {len(dropped)} bang.")

    print(">> Dang dung lai schema + seed admin + 10 don vi chuan...")
    # Import app.main lam dung viec cua lan khoi dong dau tien:
    #   Base.metadata.create_all() + ensure_system_admin() + ensure_standard_units()
    import app.main  # noqa: F401  (side-effect: tao bang + seed)

    after = _row_counts()
    print("\n=== KET QUA ===")
    print(f"Tong so bang     : {len(after)}")
    print(f"users            : {after.get('users', 'N/A')}  (ky vong 1 - admin)")
    print(f"units            : {after.get('units', 'N/A')}  (ky vong 10)")
    leftover = {k: v for k, v in after.items() if v and k not in ("users", "units")}
    if leftover:
        print(f"CANH BAO - bang van con du lieu: {leftover}")
    else:
        print("Cac bang nghiep vu khac: rong.")

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, username, role, is_active, is_system FROM users")).all()
    print("\nTai khoan con lai:")
    for r in rows:
        print(f"    id={r[0]}  username={r[1]!r}  role={r[2]}  is_active={r[3]}  is_system={r[4]}")

    print(
        f"\nDANG NHAP: {settings.SYSTEM_ADMIN_USERNAME} / "
        f"{settings.SYSTEM_ADMIN_PASSWORD}  (doi ngay sau khi vao)"
    )
    print("Nho KHOI DONG LAI backend (uvicorn) de lam moi pool ket noi.")


if __name__ == "__main__":
    main()
