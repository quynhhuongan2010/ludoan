"""Migration thu cong: doi `users.role` tu chuoi -> so nguyen 0..5.

`Base.metadata.create_all` khong doi kieu cot cua bang cu -> can script nay.
Idempotent, KHONG xoa du lieu. Chay sau `migrate_rank_position.py`:

    venv/Scripts/python.exe scripts/migrate_role_to_int.py

Anh xa gia tri cu -> moi (so do phan quyen "A"):
  'admin'            -> 0  (Quan tri he thong)
  'commander'        -> 1  (Lu truong - Chinh uy)   [gop toan bo chi huy cu ve muc 1]
  'officer'          -> 4  (Ca nhan)
  'soldier' (legacy) -> 5  (Nguoi dung, chi xem)
  gia tri la so san  -> giu nguyen (chay lai lan 2 khong hong)

Sau khi backfill xong: ALTER cot `role` sang INT NOT NULL DEFAULT 5.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

# Thu tu quan trong: xu ly cac gia tri chuoi truoc khi doi kieu cot.
STRING_TO_INT = [
    ("admin", 0),
    ("commander", 1),
    ("officer", 4),
    ("soldier", 5),
]


def role_column_type(conn) -> str:
    row = conn.execute(
        text(
            "SELECT DATA_TYPE FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' "
            "AND COLUMN_NAME = 'role'"
        )
    ).first()
    return (row[0] if row else "").lower()


def main() -> None:
    with engine.begin() as conn:
        dtype = role_column_type(conn)
        if not dtype:
            print("Khong tim thay cot users.role - bo qua.")
            return

        if dtype in ("int", "integer", "smallint", "tinyint", "bigint"):
            print(f"users.role da la kieu so ({dtype}) - khong lam gi (idempotent).")
            return

        print(f"users.role dang la kieu '{dtype}'. Bat dau backfill gia tri...")
        total = 0
        for old, new in STRING_TO_INT:
            res = conn.execute(
                text("UPDATE users SET role = :new WHERE role = :old"),
                {"new": str(new), "old": old},
            )
            if res.rowcount:
                print(f"  {old!r:12} -> {new}: {res.rowcount} tai khoan")
            total += res.rowcount

        # Bat ky gia tri chuoi la nao con lai (khong ro) -> 5 (Nguoi dung, an toan nhat).
        res = conn.execute(
            text("UPDATE users SET role = '5' WHERE role NOT IN ('0','1','2','3','4','5')")
        )
        if res.rowcount:
            print(f"  (gia tri la khac)  -> 5: {res.rowcount} tai khoan")
            total += res.rowcount

        conn.execute(
            text("ALTER TABLE users MODIFY COLUMN role INT NOT NULL DEFAULT 5")
        )
        print(f"Da doi kieu cot users.role -> INT NOT NULL DEFAULT 5. Tong backfill: {total}.")
        print("Luu y: toan bo tai khoan chi huy cu (commander) da ve muc 1 (Lu truong -")
        print("Chinh uy). Chi huy/admin can chinh lai muc 2/3 cho dung chuc trach qua")
        print("PATCH /users/{id}/role.")


if __name__ == "__main__":
    main()
