"""Migration thu cong: bo sung truong van thu cho `official_dispatches`.

`Base.metadata.create_all` chi tao bang moi, KHONG them cot vao bang cu -> can
script nay cho DB da co bang `official_dispatches`. Idempotent, KHONG xoa du lieu.

    venv/Scripts/python.exe scripts/migrate_dispatch_doc_type.py

Them cac cot con thieu:
  - doc_type       VARCHAR(20) NOT NULL DEFAULT 'cong_van'  (loai van ban)
  - signer         VARCHAR(200) NULL                        (nguoi ky)
  - deadline       DATE NULL                                (han xu ly / tra loi)
  - page_count     INT NULL                                 (so to)
  - security_level VARCHAR(20) NOT NULL DEFAULT 'mat'        (do mat)
  - urgency        VARCHAR(20) NOT NULL DEFAULT 'thuong'     (do khan)
  - archive_ref    VARCHAR(120) NULL                        (so ho so luu tru)

Ban ghi cu -> doc_type='cong_van', security_level='mat', urgency='thuong'.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

TABLE = "official_dispatches"
COLUMNS = {
    "doc_type": "VARCHAR(20) NOT NULL DEFAULT 'cong_van'",
    "signer": "VARCHAR(200) NULL",
    "deadline": "DATE NULL",
    "page_count": "INT NULL",
    "security_level": "VARCHAR(20) NOT NULL DEFAULT 'mat'",
    "urgency": "VARCHAR(20) NOT NULL DEFAULT 'thuong'",
    "archive_ref": "VARCHAR(120) NULL",
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
        have = cols(conn, TABLE)
        added = []
        for name, ddl in COLUMNS.items():
            if name not in have:
                conn.execute(text(f"ALTER TABLE {TABLE} ADD COLUMN `{name}` {ddl}"))
                added.append(name)

    print(f"{TABLE} (cot moi) : {added or 'khong co (da day du)'}")
    print("Hoan tat. Ban ghi cu: doc_type='cong_van', security_level='mat', urgency='thuong'.")


if __name__ == "__main__":
    main()
