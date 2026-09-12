# -*- coding: utf-8 -*-
"""Xoa sach TOAN BO du lieu he Tin nhan Tac chien noi bo (chat) - KHONG dung
den bat ky bang nao khac (users / units / posts / ...).

Xoa theo thu tu an toan khoa ngoai:
    chat_message_reactions -> chat_messages -> chat_participants -> chat_conversations

Dung khi: don dep du lieu chat thu nghiem truoc khi ban giao / truoc khi chup
lai anh huong dan (`capture_chat_guide.py` tu gieo + tu don du lieu `(demo)`).

Chay tu backend/:
    venv/Scripts/python.exe scripts/reset_chat_data.py           # xoa that
    venv/Scripts/python.exe scripts/reset_chat_data.py --dry-run # chi dem
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

# Thu tu xoa: bang con truoc, bang cha sau.
TABLES = [
    "chat_message_reactions",
    "chat_messages",
    "chat_participants",
    "chat_conversations",
]

# Tep dinh kem tin nhan chat luu duoi storage/uploads/chat/
UPLOAD_CHAT_DIR = pathlib.Path(__file__).resolve().parent.parent / "storage" / "uploads" / "chat"


def _count(conn, table: str) -> int:
    try:
        return conn.execute(text(f"SELECT COUNT(*) FROM `{table}`")).scalar() or 0
    except Exception:  # noqa: BLE001 - bang chua ton tai
        return -1


def main() -> None:
    dry = "--dry-run" in sys.argv[1:]

    with engine.begin() as conn:
        before = {t: _count(conn, t) for t in TABLES}
        print("Truoc khi xoa:")
        for t, n in before.items():
            print(f"  {t:26} {n if n >= 0 else '(khong co bang)'}")

        if dry:
            print("\n[--dry-run] Khong xoa gi.")
            return

        # MySQL: tat kiem tra FK tam thoi cho chac (thu tu tren da an toan roi)
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        removed = {}
        for t in TABLES:
            if before[t] < 0:
                continue
            conn.execute(text(f"DELETE FROM `{t}`"))
            try:
                conn.execute(text(f"ALTER TABLE `{t}` AUTO_INCREMENT = 1"))
            except Exception:  # noqa: BLE001
                pass
            removed[t] = before[t]
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    # Don tep dinh kem chat tren dia
    n_files = 0
    if UPLOAD_CHAT_DIR.is_dir():
        for f in UPLOAD_CHAT_DIR.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                    n_files += 1
                except OSError:
                    pass

    print("\nDa xoa:")
    for t, n in removed.items():
        print(f"  {t:26} {n} dong")
    print(f"  tep dinh kem chat tren dia   {n_files} tep")
    print("\nXong. He Tin nhan da o trang thai sach.")


if __name__ == "__main__":
    main()
