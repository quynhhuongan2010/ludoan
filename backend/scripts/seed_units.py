"""Khoi tao co cau to chuc chuan cua Lu doan Thong tin 21 (bang `units`).

Idempotent - chi tao don vi con THIEU (so khop theo ten), khong dung den don vi
da co. Chay 1 lan sau khi trien khai, hoac chay lai bat cu luc nao:

    backend/venv/Scripts/python.exe scripts/seed_units.py

Cac dau moi nay dung de:
  - Gan tai khoan vao dung don vi (Quan ly nguoi dung / Quan ly don vi).
  - Giao nhiem vu xuong tung dau moi va nhan bao cao qua Kenh Chi dao - Bao cao.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.bootstrap import ensure_standard_units  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.unit import Unit  # noqa: E402


def main() -> None:
    with SessionLocal() as db:
        added = ensure_standard_units(db)
        total = db.query(Unit).count()
    if added:
        print("Đã thêm các đơn vị:")
        for n in added:
            print("  +", n)
    else:
        print("Không có đơn vị nào cần thêm (đã đầy đủ).")
    print(f"Tổng số đơn vị hiện có: {total}")


if __name__ == "__main__":
    main()
