"""Xoa 2 bang chet cua tinh nang "Giao ban truc tuyen" da bi go bo (openapi v7.0.0).

`Base.metadata.create_all` khong bao gio DROP bang, nen sau khi go model
`command_meeting` thi 2 bang duoi day (neu DB da tung tao) chi con nam khong.
Chay 1 lan de don sach:

    venv/Scripts/python.exe scripts/drop_command_meetings.py

Idempotent: chay lai khi bang da bi xoa cung khong bao loi.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

# Xoa bang con (co FK toi command_meetings) truoc, roi bang cha.
_TABLES = ("command_meeting_attendees", "command_meetings")


def main() -> None:
    with engine.begin() as conn:
        for table in _TABLES:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            print(f"  [drop] {table}")
    print("Xong. Da go 2 bang cua tinh nang Giao ban truc tuyen.")


if __name__ == "__main__":
    main()
