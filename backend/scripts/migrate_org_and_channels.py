"""Migration thu cong: bang `units` + cac cot to chuc / kenh han che tren `users`.

`Base.metadata.create_all` chi tao bang moi, khong them cot vao bang cu -> can script nay.
Idempotent, KHONG xoa du lieu. Chay SAU `migrate_access_tiers.py`:

    venv/Scripts/python.exe scripts/migrate_org_and_channels.py

Them:
  - Bang `units` (neu chua co)
  - users.unit_id                    (FK units.id, nullable)
  - users.directive_channel_access   (mac dinh 0)
  - users.command_channel_access     (mac dinh 0)
  - users.is_system                  (mac dinh 0)
  - users.must_change_password       (mac dinh 0)
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

CREATE_UNITS = """
CREATE TABLE IF NOT EXISTS units (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    unit_kind VARCHAR(30) NOT NULL DEFAULT 'phong_ban',
    description VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_units_name (name),
    KEY ix_units_unit_kind (unit_kind)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

USERS_COLUMNS = {
    "unit_id": "INT NULL",
    "directive_channel_access": "TINYINT(1) NOT NULL DEFAULT 0",
    "command_channel_access": "TINYINT(1) NOT NULL DEFAULT 0",
    "is_system": "TINYINT(1) NOT NULL DEFAULT 0",
    "must_change_password": "TINYINT(1) NOT NULL DEFAULT 0",
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
        conn.execute(text(CREATE_UNITS))

        have = cols(conn, "users")
        added = []
        for name, ddl in USERS_COLUMNS.items():
            if name not in have:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
                added.append(name)

        if "unit_id" in added:
            try:
                conn.execute(text("CREATE INDEX ix_users_unit_id ON users (unit_id)"))
            except Exception:  # noqa: BLE001
                pass
            try:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD CONSTRAINT fk_users_unit "
                        "FOREIGN KEY (unit_id) REFERENCES units (id)"
                    )
                )
            except Exception:  # noqa: BLE001 - FK co the da ton tai
                pass

    print("units       : da tao / xac nhan")
    print(f"users       : {added or 'khong co (da day du)'}")
    print("Hoan tat.")


if __name__ == "__main__":
    main()
