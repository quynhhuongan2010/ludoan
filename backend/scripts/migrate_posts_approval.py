"""Migration thu cong: them cot luong duyet bai vao bang `posts` da ton tai.

Vi sao can: `Base.metadata.create_all` chi tao bang moi, khong them cot vao bang cu.
Script nay idempotent (chay lai nhieu lan khong loi) va KHONG xoa du lieu:
  - Them cot: status, review_note, reviewed_by_id, reviewed_at
  - Backfill: moi bai hien co -> status = 'da_duyet' (truoc day dang la hien thi ngay)

Chay:
    venv/Scripts/python.exe scripts/migrate_posts_approval.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

COLUMNS = {
    "status": "VARCHAR(20) NOT NULL DEFAULT 'cho_duyet'",
    "review_note": "VARCHAR(500) NULL",
    "reviewed_by_id": "INT NULL",
    "reviewed_at": "DATETIME NULL",
}


def existing_columns(conn) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'posts'"
        )
    )
    return {r[0] for r in rows}


def main() -> None:
    with engine.begin() as conn:
        have = existing_columns(conn)
        added = []
        for name, ddl in COLUMNS.items():
            if name not in have:
                conn.execute(text(f"ALTER TABLE posts ADD COLUMN {name} {ddl}"))
                added.append(name)

        if "status" in added:
            # Bai da ton tai truoc khi co luong duyet -> coi nhu da duyet.
            conn.execute(text("UPDATE posts SET status = 'da_duyet'"))

        # Tao index cho status neu chua co (bo qua loi neu da co).
        try:
            conn.execute(text("CREATE INDEX ix_posts_status ON posts (status)"))
        except Exception:  # noqa: BLE001 - index co the da ton tai
            pass

    print(f"Hoan tat. Cot da them: {added or 'khong co (da day du tu truoc)'}")


if __name__ == "__main__":
    main()
