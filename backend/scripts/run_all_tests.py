"""Chay tuan tu toan bo bo kiem thu backend va in bang tong hop ket qua.

Thu tu chay (theo TASK_BACKLOG_BE.md - Task BE-02):
    1. python -m scripts.test_post_rbac        (RBAC + bac phan loai - SQLite in-memory)
    2. python -m scripts.test_full_system      (E2E 5 Phase - uvicorn that + MySQL that)
    3. python -m scripts.test_content_modules  (E2E cac module noi dung - uvicorn + MySQL)

Mac dinh: DUNG NGAY khi mot script that bai (exit code != 0). Dung `--keep-going`
de chay het roi moi bao loi.

Chay:
    backend/venv/Scripts/python.exe scripts/run_all_tests.py
    hoac:  python -m scripts.run_all_tests [--keep-going]

Exit code: 0 neu tat ca PASS, 1 neu co bat ky script nao FAIL.
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # thu muc backend/

# (nhan hien thi, module chay qua `-m`)
SUITES = [
    ("test_post_rbac", "scripts.test_post_rbac"),
    ("test_full_system", "scripts.test_full_system"),
    ("test_content_modules", "scripts.test_content_modules"),
    ("test_chat_features", "scripts.test_chat_features"),
]

_RESULT_LINE = re.compile(r"PASS:\s*(\d+)\s*\|\s*FAIL:\s*(\d+)", re.IGNORECASE)
_RBAC_FAIL = re.compile(r"KET QUA:\s*(\d+)\s*FAIL", re.IGNORECASE)
_RBAC_OK = re.compile(r"KET QUA:\s*TAT CA PASS", re.IGNORECASE)


def _count_from_output(text: str) -> "tuple[int | None, int | None]":
    """Rut so luong PASS / FAIL tu output cua script (neu doc duoc)."""
    m = _RESULT_LINE.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))
    if _RBAC_OK.search(text):
        n_pass = len(re.findall(r"(?m)^PASS ", text))
        return n_pass, 0
    m = _RBAC_FAIL.search(text)
    if m:
        n_pass = len(re.findall(r"(?m)^PASS ", text))
        return n_pass, int(m.group(1))
    return None, None


def run_suite(label: str, module: str) -> dict:
    print("\n" + "#" * 78)
    print(f"#  DANG CHAY: python -m {module}")
    print("#" * 78, flush=True)

    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")

    started = time.time()
    proc = subprocess.Popen(
        [sys.executable, "-m", module],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    chunks: list = []
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        chunks.append(line)
    proc.wait()
    elapsed = time.time() - started

    n_pass, n_fail = _count_from_output("".join(chunks))
    return {
        "label": label,
        "module": module,
        "exit": proc.returncode,
        "ok": proc.returncode == 0,
        "elapsed": elapsed,
        "n_pass": n_pass,
        "n_fail": n_fail,
    }


def print_summary(results: list) -> None:
    print("\n" + "=" * 78)
    print("  BANG TONG HOP KET QUA KIEM THU BACKEND")
    print("=" * 78)
    header = f"  {'#':<3}{'Script':<24}{'Ket qua':<10}{'Pass':>6}{'Fail':>6}{'Giay':>9}{'Exit':>6}"
    print(header)
    print("  " + "-" * 74)
    total_pass = total_fail = 0
    for i, r in enumerate(results, 1):
        verdict = "PASS" if r["ok"] else "FAIL"
        p = "-" if r["n_pass"] is None else str(r["n_pass"])
        f = "-" if r["n_fail"] is None else str(r["n_fail"])
        total_pass += r["n_pass"] or 0
        total_fail += r["n_fail"] or 0
        print(f"  {i:<3}{r['label']:<24}{verdict:<10}{p:>6}{f:>6}{r['elapsed']:>9.1f}{r['exit']:>6}")
    print("  " + "-" * 74)
    print(f"  {'':<3}{'TONG (test case doc duoc)':<24}{'':<10}{total_pass:>6}{total_fail:>6}")

    skipped = [s[0] for s in SUITES if s[0] not in {r["label"] for r in results}]
    if skipped:
        print(f"\n  Bo qua (do dung som): {', '.join(skipped)}")

    all_ok = all(r["ok"] for r in results) and not skipped
    print("\n  => " + ("TAT CA SCRIPT PASS." if all_ok else "CO SCRIPT THAT BAI - xem chi tiet o tren."))


def main() -> int:
    keep_going = "--keep-going" in sys.argv[1:]

    print("CHAY TOAN BO KIEM THU BACKEND  |  keep_going =", keep_going)
    print("  Thu muc lam viec:", ROOT)

    results: list = []
    for label, module in SUITES:
        r = run_suite(label, module)
        results.append(r)
        if not r["ok"] and not keep_going:
            print(f"\n!!! '{label}' THAT BAI (exit {r['exit']}) - DUNG QUY TRINH "
                  f"(dung --keep-going de chay tiep).")
            break

    print_summary(results)
    failed = any(not r["ok"] for r in results) or len(results) < len(SUITES)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
