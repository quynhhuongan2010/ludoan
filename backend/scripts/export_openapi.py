"""Xuat OpenAPI schema cua backend ra file openapi.yaml o thu muc goc du an.

Chay sau moi lan them/sua endpoint de dong bo hop dong API voi Frontend:
    venv/Scripts/python.exe scripts/export_openapi.py

Khong can server dang chay: script import truc tiep app va goi app.openapi().
File xuat ra co header ghi chu: phien ban API + thoi diem sinh + so endpoint,
de FE biet co dung ban moi nhat khong (xem them openapi.CHANGELOG.md).
"""

import datetime
import pathlib
import sys

import yaml

# Cho phep import goi `app` khi chay truc tiep tu thu muc backend/
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = ROOT / "openapi.yaml"


def main() -> None:
    spec = app.openapi()
    version = spec.get("info", {}).get("version", "?")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n_paths = len(spec["paths"])
    n_ops = sum(len(v) for v in spec["paths"].values())

    header = (
        "# ==========================================================\n"
        f"#  HOP DONG API - Quynh Web  |  phien ban: {version}\n"
        f"#  Sinh luc: {now}  |  {n_paths} path, {n_ops} operation\n"
        "#  Lich su thay doi: openapi.CHANGELOG.md (cung thu muc)\n"
        "#  File nay sinh tu backend - KHONG sua tay.\n"
        "# ==========================================================\n"
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.dump(spec, f, allow_unicode=True, sort_keys=False)

    print(f"Da xuat phien ban {version}: {n_paths} path / {n_ops} operation -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
