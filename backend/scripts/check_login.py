"""Chan doan / khac phuc loi dang nhap "Invalid username or password".

Chay tay trong venv cua backend:

    # 1) Xem toan bo tai khoan trong DB
    venv\\Scripts\\python.exe scripts\\check_login.py

    # 2) Kiem tra 1 cap tai khoan / mat khau co dang nhap duoc khong (khong doi gi)
    venv\\Scripts\\python.exe scripts\\check_login.py --user admin --password admin

    # 3) Dat lai mat khau cho 1 tai khoan (vd mo lai admin)
    venv\\Scripts\\python.exe scripts\\check_login.py --user admin --set-password "MatKhauMoi123"

Script chi dung ham bam mat khau CUA CHINH app (app.core.security.hash_password)
va doc cau hinh DB tu .env — khong hardcode gi.
"""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password, verify_password  # noqa: E402
from app.models.user import User  # noqa: E402


def list_users(db) -> None:
    users = db.query(User).order_by(User.role, User.username).all()
    if not users:
        print("!! Bang `users` DANG RONG — chua co tai khoan nao.")
        print("   Khoi dong lai backend de bootstrap seed admin, hoac chay: python scripts/seed_admin.py")
        return
    print(f"Tong {len(users)} tai khoan:\n")
    print(f"  {'id':>3}  {'username':<20} {'role':>4}  {'active':<6} {'system':<6} {'must_change_pw'}")
    print(f"  {'-' * 3}  {'-' * 20} {'-' * 4}  {'-' * 6} {'-' * 6} {'-' * 13}")
    for u in users:
        print(
            f"  {u.id:>3}  {u.username:<20} {u.role:>4}  "
            f"{str(bool(u.is_active)):<6} {str(bool(u.is_system)):<6} {bool(u.must_change_password)}"
        )
    print(
        "\nLuu y: dang nhap se BAO 401 neu (a) sai username, (b) sai mat khau, "
        "hoac (c) is_active = False -> khi do bao 403 'chua kich hoat'."
    )


def check_credentials(db, username: str, password: str) -> None:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        print(f"[X] Khong tim thay tai khoan co username = {username!r} (phan biet HOA/thuong).")
        near = [u.username for u in db.query(User).all() if u.username.lower() == username.lower()]
        if near:
            print(f"    Co tai khoan gan giong (khac hoa/thuong): {near}")
        return
    ok = verify_password(password, user.hashed_password)
    print(f"[{'OK' if ok else 'X'}] username = {username!r}: mat khau {'DUNG' if ok else 'SAI'}.")
    if ok and not user.is_active:
        print("    -> Nhung tai khoan CHUA KICH HOAT (is_active = False) nen dang nhap tra 403.")
    elif ok:
        print("    -> Cap nay dang nhap duoc. Neu FE van bao loi: kiem tra o nhap co dinh khoang trang thua khong.")
    else:
        print("    -> Dat lai mat khau bang: --set-password \"<mat khau moi>\"")


def set_password(db, username: str, new_password: str) -> None:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        print(f"[X] Khong tim thay username = {username!r}. Huy.")
        return
    user.hashed_password = hash_password(new_password)
    user.is_active = True
    user.must_change_password = True
    db.add(user)
    db.commit()
    print(
        f"[OK] Da dat lai mat khau cho {username!r}. is_active=True, must_change_password=True.\n"
        f"     Dang nhap lai bang mat khau moi (he thong se yeu cau doi mat khau lan dau)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Chan doan / khac phuc loi dang nhap.")
    parser.add_argument("--user", help="username can kiem tra / dat lai mat khau")
    parser.add_argument("--password", help="mat khau can kiem tra (khong thay doi DB)")
    parser.add_argument("--set-password", dest="set_password", help="dat lai mat khau moi cho --user")
    args = parser.parse_args()

    with SessionLocal() as db:
        if args.user and args.set_password:
            set_password(db, args.user, args.set_password)
        elif args.user and args.password:
            check_credentials(db, args.user, args.password)
        else:
            list_users(db)


if __name__ == "__main__":
    main()
