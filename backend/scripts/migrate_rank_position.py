"""Migration thu cong: bo vai tro "soldier" + them Cap bac / Chuc danh cho users.

`Base.metadata.create_all` chi tao bang moi, khong them cot vao bang cu -> can
script nay. Idempotent, KHONG xoa du lieu. Chay sau `migrate_org_and_channels.py`:

    venv/Scripts/python.exe scripts/migrate_rank_position.py

Lam:
  - Them users.military_rank VARCHAR(100) NULL (Cap bac quan ham; ten cot tranh
    tu khoa dat "rank" cua MySQL 8 - xem `app/models/user.py`)
  - Them users.position      VARCHAR(150) NULL (Chuc danh cong tac)
  - UPDATE users SET role='officer' WHERE role='soldier'
    (chi can bo / QNCN co bien che moi duoc cap tai khoan mang noi bo)
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

USERS_COLUMNS = {
    "military_rank": "VARCHAR(100) NULL",
    "position": "VARCHAR(150) NULL",
}


def cols(conn, table: str) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
        ),
        {"t": table},
    )
    return {r[0] for r in rows}


def main() -> None:
    with engine.begin() as conn:
        have = cols(conn, "users")
        added = []
        for name, ddl in USERS_COLUMNS.items():
            if name not in have:
                # Bao ten cot trong backtick: `rank` la tu khoa dat trong MySQL 8
                # (ham window RANK()), ALTER TABLE se loi cu phap neu khong quote.
                conn.execute(text(f"ALTER TABLE users ADD COLUMN `{name}` {ddl}"))
                added.append(name)

        result = conn.execute(text("UPDATE users SET role = 'officer' WHERE role = 'soldier'"))
        migrated = result.rowcount

    print(f"users (cot moi) : {added or 'khong co (da day du)'}")
    print(f"users role      : {migrated} tai khoan 'soldier' -> 'officer'")
    print("Hoan tat. Luu y: tai khoan da chuyen sang officer con thieu Cap bac/Chuc")
    print("danh/Don vi se khong kich hoat lai duoc cho toi khi chi huy bo sung qua")
    print("PATCH /users/{id}/info va PATCH /users/{id}/unit.")


if __name__ == "__main__":
    main()
