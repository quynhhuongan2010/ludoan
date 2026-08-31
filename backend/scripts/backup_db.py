"""Sao luu tu dong CSDL MySQL ra file .sql nen (gzip), doc cau hinh tu .env.

Chay tay:
    venv/Scripts/python.exe scripts/backup_db.py

Chay dinh ky (khuyen nghi, xem huong dan trong trang "Huong dan su dung" ->
tab "Cam nang xu ly su co" cua he thong): dang ky Windows Task Scheduler goi
lai chinh lenh tren, vi du moi ngay luc 23:00.

Khong hardcode mat khau: doc MYSQL_HOST/PORT/DATABASE/USER/PASSWORD tu
`.env` (qua `app.core.config.settings`, dung chung voi backend). Mat khau
duoc truyen cho `mysqldump` qua bien moi truong MYSQL_PWD (khong qua tham so
dong lenh) de khong hien trong danh sach tien trinh (Task Manager/`ps`).

Ket qua: `storage/backups/<ten_db>_YYYYmmdd_HHMMSS.sql.gz`. Tu dong don dep,
chi giu lai N ban gan nhat (mac dinh 14 - xem BACKUP_RETENTION o duoi) de
khong lam day o dia qua thoi gian.

Phuc hoi du lieu tu ban sao luu:
    gzip -d < storage\\backups\\ludoan_db_20260830_230000.sql.gz | mysql -u <user> -p <ten_db>
hoac tren Windows (khong co lenh gzip san):
    venv\\Scripts\\python.exe scripts\\backup_db.py --restore storage\\backups\\ludoan_db_20260830_230000.sql.gz
"""

from __future__ import annotations

import argparse
import datetime
import gzip
import os
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402

# So ban sao luu gan nhat duoc giu lai (moi ban ~vai chuc KB - vai MB tuy du
# lieu). Doi bang bien moi truong BACKUP_RETENTION neu can giu nhieu/it hon.
BACKUP_RETENTION = int(os.environ.get("BACKUP_RETENTION", "14"))

BACKUP_DIR = pathlib.Path(__file__).resolve().parent.parent / "storage" / "backups"

# Cac vi tri thuong gap cua mysqldump.exe tren Windows neu chua co san trong PATH.
_COMMON_MYSQL_BIN_GLOBS = [
    r"C:\Program Files\MySQL\MySQL Server *\bin\mysqldump.exe",
    r"C:\Program Files\MySQL\MySQL Server * \bin\mysqldump.exe",
    r"C:\xampp\mysql\bin\mysqldump.exe",
    r"C:\wamp64\bin\mysql\mysql*\bin\mysqldump.exe",
]


def find_tool(name: str) -> str:
    """Tim duong dan toi `mysqldump`/`mysql`: uu tien PATH, sau do do quet cac
    thu muc cai dat pho bien tren Windows."""
    found = shutil.which(name)
    if found:
        return found
    for pattern in _COMMON_MYSQL_BIN_GLOBS:
        pattern = pattern.replace("mysqldump.exe", f"{name}.exe")
        matches = sorted(pathlib.Path("C:/").glob(pattern.replace("C:\\", "").replace("\\", "/")))
        if matches:
            return str(matches[-1])
    raise FileNotFoundError(
        f"Khong tim thay '{name}.exe'. Cai dat MySQL Client hoac them thu muc "
        "chua no (vd C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin) vao bien "
        "moi truong PATH cua Windows, roi thu lai."
    )


def backup() -> pathlib.Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    mysqldump = find_tool("mysqldump")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = BACKUP_DIR / f"{settings.MYSQL_DATABASE}_{timestamp}.sql.gz"

    cmd = [
        mysqldump,
        f"--host={settings.MYSQL_HOST}",
        f"--port={settings.MYSQL_PORT}",
        f"--user={settings.MYSQL_USER}",
        "--single-transaction",  # khong khoa bang, an toan khi he thong dang chay
        "--routines",
        "--triggers",
        "--default-character-set=utf8mb4",
        settings.MYSQL_DATABASE,
    ]
    # Truyen mat khau qua bien moi truong (khong qua tham so dong lenh) de
    # khong lo trong danh sach tien trinh.
    env = {**os.environ, "MYSQL_PWD": settings.MYSQL_PASSWORD}

    print(f"Dang sao luu CSDL '{settings.MYSQL_DATABASE}' tu {settings.MYSQL_HOST}:{settings.MYSQL_PORT}...")
    # Luu y: KHONG duoc truyen thang doi tuong gzip.GzipFile lam `stdout=` cho
    # subprocess.run - subprocess se dup2() thang vao file descriptor goc cua
    # no (bo qua lop nen cua Python), ket qua ghi ra file .sql THO khong nen
    # du co duoi .gz. Phai dung Popen(stdout=PIPE) roi tu doc/ghi qua gzip.
    with gzip.open(out_path, "wb") as gz_file:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        assert proc.stdout is not None
        shutil.copyfileobj(proc.stdout, gz_file)
        _, stderr = proc.communicate()

    if proc.returncode != 0:
        out_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"mysqldump loi (ma {proc.returncode}): {stderr.decode('utf-8', errors='replace')}"
        )

    size_kb = out_path.stat().st_size / 1024
    print(f"Da sao luu thanh cong: {out_path}  ({size_kb:,.1f} KB)")
    return out_path


def cleanup_old_backups(retention: int = BACKUP_RETENTION) -> None:
    if not BACKUP_DIR.is_dir():
        return
    files = sorted(
        BACKUP_DIR.glob(f"{settings.MYSQL_DATABASE}_*.sql.gz"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    stale = files[retention:]
    for f in stale:
        f.unlink()
    if stale:
        print(f"Da xoa {len(stale)} ban sao luu cu (chi giu {retention} ban gan nhat).")


def restore(archive_path: str) -> None:
    """Phuc hoi CSDL tu 1 file .sql.gz da sao luu. CANH BAO: ghi de du lieu
    hien tai trong CSDL dich (khong tu xoa CSDL - cac bang trung ten se bi
    ghi de theo noi dung file sao luu)."""
    src = pathlib.Path(archive_path)
    if not src.is_file():
        raise FileNotFoundError(f"Khong tim thay file sao luu: {src}")

    mysql = find_tool("mysql")
    env = {**os.environ, "MYSQL_PWD": settings.MYSQL_PASSWORD}
    cmd = [
        mysql,
        f"--host={settings.MYSQL_HOST}",
        f"--port={settings.MYSQL_PORT}",
        f"--user={settings.MYSQL_USER}",
        "--default-character-set=utf8mb4",
        settings.MYSQL_DATABASE,
    ]

    print(f"CANH BAO: sap ghi de du lieu vao CSDL '{settings.MYSQL_DATABASE}' tu {src.name}")
    confirm = input("Go 'YES' de tiep tuc: ")
    if confirm.strip() != "YES":
        print("Da huy phuc hoi.")
        return

    # Tuong tu ham backup(): phai giai nen qua Python (gzip.open doc) roi moi
    # ghi vao stdin cua tien trinh con - khong duoc truyen thang file .gz cho
    # subprocess (no se dup2() fd goc, doc phai du lieu da nen chua giai ma).
    with gzip.open(src, "rb") as gz_file:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        assert proc.stdin is not None
        shutil.copyfileobj(gz_file, proc.stdin)
        proc.stdin.close()
        _, stderr = proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(
            f"Phuc hoi that bai (ma {proc.returncode}): {stderr.decode('utf-8', errors='replace')}"
        )
    print("Phuc hoi CSDL thanh cong.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--restore",
        metavar="FILE.sql.gz",
        help="Phuc hoi CSDL tu file sao luu thay vi tao ban sao luu moi.",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=BACKUP_RETENTION,
        help=f"So ban sao luu gan nhat duoc giu lai (mac dinh {BACKUP_RETENTION}).",
    )
    args = parser.parse_args()

    if args.restore:
        restore(args.restore)
        return

    backup()
    cleanup_old_backups(args.retention)


if __name__ == "__main__":
    main()
