# -*- coding: utf-8 -*-
"""Migration: tinh nang chat nang cao (v8.1.0).

Them cot vao bang cu (create_all khong them cot cho bang da ton tai) va tao
bang moi `chat_message_reactions`. Idempotent: bo qua cot / index / FK / bang
da co.

`chat_messages`:
- message_type       VARCHAR(20)  NOT NULL DEFAULT 'user'
- reply_to_id        INT          NULL   (FK chat_messages.id)
- forwarded_from_id  INT          NULL   (FK chat_messages.id)
- is_edited          TINYINT(1)   NOT NULL DEFAULT 0
- edited_at          DATETIME     NULL
- is_recalled        TINYINT(1)   NOT NULL DEFAULT 0
- recalled_at        DATETIME     NULL
- is_pinned          TINYINT(1)   NOT NULL DEFAULT 0   (index)
- pinned_at          DATETIME     NULL
- pinned_by_id       INT          NULL   (FK users.id)

`chat_participants`:
- last_read_message_id  INT        NOT NULL DEFAULT 0
- is_muted              TINYINT(1) NOT NULL DEFAULT 0
- is_archived           TINYINT(1) NOT NULL DEFAULT 0

`chat_message_reactions` (bang moi):
- id, message_id (FK chat_messages.id ON DELETE CASCADE), user_id (FK users.id),
  emoji VARCHAR(16), created_at DATETIME; UNIQUE(message_id, user_id, emoji).

Chay:
    venv/Scripts/python.exe scripts/migrate_chat_features.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

MSG_TABLE = "chat_messages"
PART_TABLE = "chat_participants"
REACT_TABLE = "chat_message_reactions"

MSG_COLUMNS = [
    ("message_type", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `message_type` VARCHAR(20) NOT NULL DEFAULT 'user'"),
    ("reply_to_id", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `reply_to_id` INT NULL"),
    ("forwarded_from_id", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `forwarded_from_id` INT NULL"),
    ("is_edited", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `is_edited` TINYINT(1) NOT NULL DEFAULT 0"),
    ("edited_at", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `edited_at` DATETIME NULL"),
    ("is_recalled", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `is_recalled` TINYINT(1) NOT NULL DEFAULT 0"),
    ("recalled_at", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `recalled_at` DATETIME NULL"),
    ("is_pinned", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `is_pinned` TINYINT(1) NOT NULL DEFAULT 0"),
    ("pinned_at", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `pinned_at` DATETIME NULL"),
    ("pinned_by_id", f"ALTER TABLE `{MSG_TABLE}` ADD COLUMN `pinned_by_id` INT NULL"),
]

PART_COLUMNS = [
    ("last_read_message_id", f"ALTER TABLE `{PART_TABLE}` ADD COLUMN `last_read_message_id` INT NOT NULL DEFAULT 0"),
    ("is_muted", f"ALTER TABLE `{PART_TABLE}` ADD COLUMN `is_muted` TINYINT(1) NOT NULL DEFAULT 0"),
    ("is_archived", f"ALTER TABLE `{PART_TABLE}` ADD COLUMN `is_archived` TINYINT(1) NOT NULL DEFAULT 0"),
]

# (ten_fk, cot, bang_dich, cot_dich, dieu_khoan_them)
# ON DELETE SET NULL: xoa cung 1 hoi thoai khong bi chan boi tin dang duoc
# hoi thoai khac tra loi / chuyen tiep; xoa user khong bi chan boi pinned_by.
MSG_FKS = [
    ("fk_chat_messages_reply_to", "reply_to_id", "chat_messages", "id", "ON DELETE SET NULL"),
    ("fk_chat_messages_forwarded_from", "forwarded_from_id", "chat_messages", "id", "ON DELETE SET NULL"),
    ("fk_chat_messages_pinned_by", "pinned_by_id", "users", "id", "ON DELETE SET NULL"),
]

CREATE_REACT_TABLE = f"""
CREATE TABLE IF NOT EXISTS `{REACT_TABLE}` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `message_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `emoji` VARCHAR(16) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_chat_message_reaction` (`message_id`, `user_id`, `emoji`),
    KEY `ix_chat_message_reactions_message_id` (`message_id`),
    KEY `ix_chat_message_reactions_user_id` (`user_id`),
    CONSTRAINT `fk_chat_message_reactions_message` FOREIGN KEY (`message_id`)
        REFERENCES `chat_messages` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_chat_message_reactions_user` FOREIGN KEY (`user_id`)
        REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""".strip()


def _existing_columns(conn, table: str) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
        ),
        {"t": table},
    ).all()
    return {r[0] for r in rows}


def _table_exists(conn, table: str) -> bool:
    rows = conn.execute(
        text(
            "SELECT 1 FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
        ),
        {"t": table},
    ).all()
    return bool(rows)


def _index_exists(conn, table: str, name: str) -> bool:
    rows = conn.execute(
        text(
            "SELECT 1 FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i"
        ),
        {"t": table, "i": name},
    ).all()
    return bool(rows)


def _fk_delete_rule(conn, table: str, name: str) -> "str | None":
    """Tra ve DELETE_RULE cua FK ('SET NULL' / 'RESTRICT' / 'NO ACTION' / ...) hoac None neu FK chua co."""
    rows = conn.execute(
        text(
            "SELECT DELETE_RULE FROM information_schema.REFERENTIAL_CONSTRAINTS "
            "WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = :t AND CONSTRAINT_NAME = :c"
        ),
        {"t": table, "c": name},
    ).all()
    return rows[0][0] if rows else None


def _add_columns(conn, table: str, columns) -> list[str]:
    have = _existing_columns(conn, table)
    if not have:
        raise SystemExit(
            f"Khong thay bang `{table}` — chay backend mot lan de create_all tao bang truoc."
        )
    added: list[str] = []
    for col, ddl in columns:
        if col in have:
            print(f"  [bo qua] {table}.{col} da co")
            continue
        conn.execute(text(ddl))
        added.append(col)
        print(f"  [them]   {table}.{col}")
    return added


def main() -> None:
    with engine.begin() as conn:
        added_msg = _add_columns(conn, MSG_TABLE, MSG_COLUMNS)
        added_part = _add_columns(conn, PART_TABLE, PART_COLUMNS)

        # Index cho is_pinned
        if not _index_exists(conn, MSG_TABLE, "ix_chat_messages_is_pinned"):
            conn.execute(
                text(f"CREATE INDEX `ix_chat_messages_is_pinned` ON `{MSG_TABLE}` (`is_pinned`)")
            )
            print("  [them]   index ix_chat_messages_is_pinned")
        else:
            print("  [bo qua] index ix_chat_messages_is_pinned da co")

        # FK tren chat_messages - dam bao DELETE_RULE = 'SET NULL'
        want_rule = "SET NULL"
        for name, col, ref_t, ref_c, extra in MSG_FKS:
            rule = _fk_delete_rule(conn, MSG_TABLE, name)
            if rule == want_rule:
                print(f"  [bo qua] FK {name} (DELETE_RULE={rule}) da dung")
                continue
            if rule is not None:
                conn.execute(text(f"ALTER TABLE `{MSG_TABLE}` DROP FOREIGN KEY `{name}`"))
                print(f"  [sua]    FK {name}: DELETE_RULE {rule} -> {want_rule} (drop + recreate)")
            conn.execute(
                text(
                    f"ALTER TABLE `{MSG_TABLE}` ADD CONSTRAINT `{name}` "
                    f"FOREIGN KEY (`{col}`) REFERENCES `{ref_t}` (`{ref_c}`) {extra}".strip()
                )
            )
            if rule is None:
                print(f"  [them]   FK {name}")

        # Bang chat_message_reactions
        if _table_exists(conn, REACT_TABLE):
            print(f"  [bo qua] bang `{REACT_TABLE}` da co")
        else:
            conn.execute(text(CREATE_REACT_TABLE))
            print(f"  [them]   bang `{REACT_TABLE}`")

        # Backfill an toan (hang cu neu default chua ap)
        conn.execute(
            text(
                f"UPDATE `{MSG_TABLE}` SET `message_type` = 'user' "
                "WHERE `message_type` IS NULL OR `message_type` = ''"
            )
        )

    total = len(added_msg) + len(added_part)
    print(f"\nXong. Da them {total} cot moi." if total else "\nXong. Khong co gi de them (da migrate truoc do).")


if __name__ == "__main__":
    main()
