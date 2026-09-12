"""Migration thu cong: them cot CMS cho bang `posts` (openapi v6.3.0).

`Base.metadata.create_all` chi tao bang moi, KHONG them cot vao bang cu -> can script nay.
Idempotent, KHONG xoa du lieu:
  - posts.summary  VARCHAR(500) NULL           (tom tat / excerpt)
  - posts.slug     VARCHAR(255) NULL UNIQUE     (slug SEO, tu sinh tu tieu de)
  - posts.tags     JSON NULL                    (the tu khoa, danh sach chuoi)

Sau khi them cot:
  - backfill posts.tags = JSON '[]' cho cac hang dang NULL (khop default=list cua model).
  - backfill posts.slug tu tieu de (bo dau tieng Viet), them hau to -2, -3... neu trung.
  - tao UNIQUE INDEX ux_posts_slug.

Trang thai moi `nhap` (ban nhap) dung chung cot `status` san co -> khong can DDL.

Chay:
    venv/Scripts/python.exe scripts/migrate_posts_cms.py
"""

import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

PLAN = {
    "summary": "VARCHAR(500) NULL",
    "slug": "VARCHAR(255) NULL",
    "tags": "JSON NULL",
}

_VN_MAP = str.maketrans(
    "àáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ",
    "aaaaaaaaaaaaaaaaadeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyy",
)


def _slugify(value: str) -> str:
    lowered = (value or "").strip().lower().translate(_VN_MAP)
    ascii_only = unicodedata.normalize("NFKD", lowered).encode("ascii", "ignore").decode()
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", ascii_only)).strip("-")


def _columns(conn, table: str) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
        ),
        {"t": table},
    )
    return {r[0] for r in rows}


def _index_exists(conn, table: str, index: str) -> bool:
    rows = conn.execute(
        text(
            "SELECT 1 FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i"
        ),
        {"t": table, "i": index},
    )
    return rows.first() is not None


def main() -> None:
    with engine.begin() as conn:
        have = _columns(conn, "posts")
        added = []
        for name, ddl in PLAN.items():
            if name not in have:
                conn.execute(text(f"ALTER TABLE posts ADD COLUMN {name} {ddl}"))
                added.append(name)

        # Backfill tags rong -> '[]'
        conn.execute(text("UPDATE posts SET tags = JSON_ARRAY() WHERE tags IS NULL"))

        # Backfill slug tu tieu de, dam bao duy nhat
        used: set[str] = {
            r[0] for r in conn.execute(text("SELECT slug FROM posts WHERE slug IS NOT NULL AND slug <> ''"))
        }
        rows = conn.execute(
            text("SELECT id, title FROM posts WHERE slug IS NULL OR slug = '' ORDER BY id")
        ).all()
        for pid, title in rows:
            base = _slugify(title) or "bai-viet"
            candidate = base
            suffix = 2
            while candidate in used:
                candidate = f"{base}-{suffix}"
                suffix += 1
            used.add(candidate)
            conn.execute(
                text("UPDATE posts SET slug = :s WHERE id = :i"), {"s": candidate, "i": pid}
            )

        if not _index_exists(conn, "posts", "ux_posts_slug"):
            conn.execute(text("CREATE UNIQUE INDEX ux_posts_slug ON posts (slug)"))

    print(f"posts: them cot {added or 'khong co (da day du)'}; da backfill tags + slug; index ux_posts_slug OK.")
    print("Hoan tat.")


if __name__ == "__main__":
    main()
