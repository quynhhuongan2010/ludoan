# -*- coding: utf-8 -*-
"""Migration: them 4 cot duyet nhom chat vao bang `chat_conversations` (v7.12.0).

- status          VARCHAR(20)  NOT NULL DEFAULT 'da_duyet'  (index)
- review_note     VARCHAR(500) NULL
- reviewed_by_id  INT          NULL  (FK users.id)
- reviewed_at     DATETIME     NULL

Idempotent: bo qua cot da ton tai. Hang cu -> status = 'da_duyet' (default).

Chay:
    venv/Scripts/python.exe scripts/migrate_chat_group_approval.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

TABLE = "chat_conversations"

# (ten_cot, cau lenh ALTER them cot)
COLUMNS = [
    ("status", f"ALTER TABLE `{TABLE}` ADD COLUMN `status` VARCHAR(20) NOT NULL DEFAULT 'da_duyet'"),
    ("review_note", f"ALTER TABLE `{TABLE}` ADD COLUMN `review_note` VARCHAR(500) NULL"),
    ("reviewed_by_id", f"ALTER TABLE `{TABLE}` ADD COLUMN `reviewed_by_id` INT NULL"),
    ("reviewed_at", f"ALTER TABLE `{TABLE}` ADD COLUMN `reviewed_at` DATETIME NULL"),
]


def _existing_columns(conn) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
        ),
        {"t": TABLE},
    ).all()
    return {r[0] for r in rows}


def _index_exists(conn, name: str) -> bool:
    rows = conn.execute(
        text(
            "SELECT 1 FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i"
        ),
        {"t": TABLE, "i": name},
    ).all()
    return bool(rows)


def _fk_exists(conn, name: str) -> bool:
    rows = conn.execute(
        text(
            "SELECT 1 FROM information_schema.TABLE_CONSTRAINTS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t "
            "AND CONSTRAINT_NAME = :c AND CONSTRAINT_TYPE = 'FOREIGN KEY'"
        ),
        {"t": TABLE, "c": name},
    ).all()
    return bool(rows)


def main() -> None:
    with engine.begin() as conn:
        have = _existing_columns(conn)
        if not have:
            raise SystemExit(
                f"Khong thay bang `{TABLE}` — chay backend mot lan de create_all tao bang truoc."
            )

        added = []
        for col, ddl in COLUMNS:
            if col in have:
                print(f"  [bo qua] cot `{col}` da co")
                continue
            conn.execute(text(ddl))
            added.append(col)
            print(f"  [them]   cot `{col}`")

        # Index cho status
        if "status" in have or "status" in added:
            if not _index_exists(conn, "ix_chat_conversations_status"):
                conn.execute(
                    text(f"CREATE INDEX `ix_chat_conversations_status` ON `{TABLE}` (`status`)")
                )
                print("  [them]   index ix_chat_conversations_status")
            else:
                print("  [bo qua] index ix_chat_conversations_status da co")

        # FK reviewed_by_id -> users.id
        if "reviewed_by_id" in have or "reviewed_by_id" in added:
            if not _fk_exists(conn, "fk_chat_conversations_reviewed_by"):
                conn.execute(
                    text(
                        f"ALTER TABLE `{TABLE}` ADD CONSTRAINT `fk_chat_conversations_reviewed_by` "
                        f"FOREIGN KEY (`reviewed_by_id`) REFERENCES `users` (`id`)"
                    )
                )
                print("  [them]   FK fk_chat_conversations_reviewed_by")
            else:
                print("  [bo qua] FK fk_chat_conversations_reviewed_by da co")

        # Backfill an toan (hang cu co the NULL neu default chua ap)
        conn.execute(
            text(f"UPDATE `{TABLE}` SET `status` = 'da_duyet' WHERE `status` IS NULL OR `status` = ''")
        )

    print(f"\nXong. Da them {len(added)} cot moi." if added else "\nXong. Khong co gi de them (da migrate truoc do).")


if __name__ == "__main__":
    main()
