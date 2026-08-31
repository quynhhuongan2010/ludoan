"""Tao / xac nhan tai khoan admin he thong (chay tay, doc lap voi khoi dong app).

    venv/Scripts/python.exe scripts/seed_admin.py

Doc `SYSTEM_ADMIN_USERNAME` / `SYSTEM_ADMIN_PASSWORD` tu `.env`.
Chi tao khi chua co tai khoan `is_system` nao (xem `app/core/bootstrap.py`).
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.bootstrap import ensure_system_admin  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402


def main() -> None:
    with SessionLocal() as db:
        user = ensure_system_admin(db)
    if user is None:
        print("Da co tai khoan admin he thong -> khong tao moi.")
    else:
        print(f"Tai khoan admin he thong: '{user.username}' (role={user.role}, must_change_password={user.must_change_password})")


if __name__ == "__main__":
    main()
