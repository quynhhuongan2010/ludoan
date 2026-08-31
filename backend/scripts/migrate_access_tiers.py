"""Migration thu cong: them cot cho co che dang ky + phan bac truy cap (cong_khai/noi_bo/mat).

`Base.metadata.create_all` chi tao bang moi, khong them cot vao bang cu -> can script nay.
Idempotent, KHONG xoa du lieu:
  - users.clearance        (mac dinh 0)
  - posts.classification   (mac dinh 'noi_bo'), posts.is_featured (mac dinh 0)
  - directives.classification (mac dinh 'noi_bo')
  - documents.classification  (mac dinh 'noi_bo'); backfill tu cot is_public cu neu con

Chay:
    venv/Scripts/python.exe scripts/migrate_access_tiers.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

# table -> {column: DDL}
PLAN = {
    "users": {
        "clearance": "TINYINT(1) NOT NULL DEFAULT 0",
    },
    "posts": {
        "classification": "VARCHAR(20) NOT NULL DEFAULT 'noi_bo'",
        "is_featured": "TINYINT(1) NOT NULL DEFAULT 0",
    },
    "directives": {
        "classification": "VARCHAR(20) NOT NULL DEFAULT 'noi_bo'",
    },
    "documents": {
        "classification": "VARCHAR(20) NOT NULL DEFAULT 'noi_bo'",
    },
}

INDEXES = {
    "posts": ["classification", "is_featured"],
    "directives": ["classification"],
    "documents": ["classification"],
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
        added_all = {}
        for table, columns in PLAN.items():
            have = cols(conn, table)
            added = []
            for name, ddl in columns.items():
                if name not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                    added.append(name)
            added_all[table] = added

        # Backfill documents.classification tu is_public cu (neu vua them cot va cot is_public con ton tai)
        if "classification" in added_all.get("documents", []):
            if "is_public" in cols(conn, "documents"):
                conn.execute(
                    text(
                        "UPDATE documents SET classification = "
                        "CASE WHEN is_public = 1 THEN 'cong_khai' ELSE 'noi_bo' END"
                    )
                )

        for table, index_cols in INDEXES.items():
            for col in index_cols:
                try:
                    conn.execute(text(f"CREATE INDEX ix_{table}_{col} ON {table} ({col})"))
                except Exception:  # noqa: BLE001 - index co the da ton tai
                    pass

    for table, added in added_all.items():
        print(f"{table:12}: {added or 'khong co (da day du)'}")
    print("Hoan tat.")


if __name__ == "__main__":
    main()
