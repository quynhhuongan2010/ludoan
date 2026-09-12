"""Kiem thu phan quyen cho POST /leadership-tasks/{id}/report (Vong 1 - F2).

Truoc khi va: bat ky tai khoan da kich hoat nao (ke ca role 5 "chi xem") cung
ghi de duoc bao cao ket qua cua moi chi dao BCH Lu doan.

Sau khi va (`leadership_task_service._can_report_on_task`):
  - role 5 (Nguoi dung)                     -> 403
  - can bo (role 4) KHONG dung don vi giao  -> 403
  - can bo (role 4) DUNG don vi giao        -> OK
  - Ban Chi huy (role 0..3)                 -> OK
  - chi dao pham vi toan_lu_doan (khong gan don vi) + can bo bat ky -> OK

Dung SQLite in-memory - KHONG dung MySQL that.
Chay tu thu muc backend/:  venv/Scripts/python.exe scripts/test_leadership_report_rbac.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.cwd()))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models.unit, app.models.user, app.models.leadership_task, app.models.audit_log  # noqa
from app.models.unit import Unit
from app.models.user import User
from app.schemas.leadership_task import (
    LeadershipTaskCreate,
    LeadershipTaskReport,
    LeadershipTaskReview,
)
from app.services import leadership_task_service as svc

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
db = sessionmaker(bind=engine)()

fails: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + label + (f"  -> {detail}" if detail else ""))
    if not cond:
        fails.append(label)


def expect_403(label: str, fn) -> None:
    try:
        fn()
        check(label, False, "khong raise (mong doi 403)")
    except HTTPException as e:
        check(label, e.status_code == 403, f"HTTP {e.status_code}: {e.detail}")


def expect_ok(label: str, fn) -> None:
    try:
        fn()
        check(label, True)
    except HTTPException as e:
        check(label, False, f"HTTP {e.status_code}: {e.detail}")


# --- du lieu ---
pham = Unit(id=1, name="Phòng Tham mưu", unit_kind="phong_ban")
d1 = Unit(id=2, name="Tiểu đoàn 1", unit_kind="tieu_doan")
d2 = Unit(id=3, name="Tiểu đoàn 2", unit_kind="tieu_doan")
db.add_all([pham, d1, d2])
db.commit()


def mk(uname, role, unit_id):
    u = User(username=uname, hashed_password="h", full_name=uname.upper(),
             role=role, is_active=True, unit_id=unit_id)
    db.add(u); db.commit(); db.refresh(u); return u


lu_truong = mk("lt", 1, 1)
chi_huy_d1 = mk("ch_d1", 3, 2)
canbo_d1 = mk("cb_d1", 4, 2)
canbo_d2 = mk("cb_d2", 4, 3)
nguoi_dung = mk("nd", 5, 2)          # role 5, dung don vi duoc giao
canbo_chinhtri = mk("cb_ct", 4, None)

# Chi dao giao cho Tieu doan 1 (assigned_unit_id=2)
task_d1 = svc.create_task(db, lu_truong, LeadershipTaskCreate(
    commander_role="lu_truong", title="Kiểm tra trực SSCĐ tại d1",
    content="Yêu cầu d1 kiểm tra 100% khí tài.", target_branch="tham_muu",
    assigned_unit_id=2, urgency="khan",
))
# Chi dao pham vi toan Lu doan, khong gan don vi
task_all = svc.create_task(db, lu_truong, LeadershipTaskCreate(
    commander_role="chinh_uy", title="Sinh hoạt chính trị quý III",
    content="Toàn Lữ đoàn quán triệt.", target_branch="toan_lu_doan",
    assigned_unit_id=None, urgency="thuong",
))

rp = LeadershipTaskReport(report_content="Đã kiểm tra xong, bảo đảm thông suốt.")

print("\n== F2: quyen nop bao cao ket qua chi dao ==")
expect_403("role 5 (Nguoi dung) nop bao cao chi dao d1 -> 403",
           lambda: svc.submit_report(db, nguoi_dung, task_d1.id, rp))
expect_403("can bo d2 (khong dung don vi giao) nop bao cao chi dao d1 -> 403",
           lambda: svc.submit_report(db, canbo_d2, task_d1.id, rp))
expect_ok("can bo d1 (dung don vi giao) nop bao cao chi dao d1 -> OK",
          lambda: svc.submit_report(db, canbo_d1, task_d1.id, rp))
expect_ok("chi huy d1 (role 3) nop bao cao chi dao d1 -> OK",
          lambda: svc.submit_report(db, chi_huy_d1, task_d1.id, rp))
expect_ok("Lu truong nop/ghi bao cao thay cho chi dao d1 -> OK",
          lambda: svc.submit_report(db, lu_truong, task_d1.id, rp))
expect_ok("can bo d2 nop bao cao chi dao pham vi toan_lu_doan -> OK",
          lambda: svc.submit_report(db, canbo_d2, task_all.id, rp))
expect_403("role 5 nop bao cao chi dao pham vi toan_lu_doan -> 403",
           lambda: svc.submit_report(db, nguoi_dung, task_all.id, rp))

print("\n== hoi quy: quyen tao / but phe khong doi ==")
expect_403("can bo d1 (role 4) ban hanh chi dao -> 403",
           lambda: svc.create_task(db, canbo_d1, LeadershipTaskCreate(
               commander_role="lu_truong", title="x x x", content="y y y y y")))
expect_403("can bo d1 (role 4) but phe duyet chi dao -> 403",
           lambda: svc.review_task(db, canbo_d1, task_d1.id,
                                   LeadershipTaskReview(status="da_hoan_thanh", review_note="ok")))

print("\n== F3: siet kieu trang thai but phe (Literal) ==")
try:
    LeadershipTaskReview(status="hoan_thanh", review_note="x")
    check("LeadershipTaskReview.status='hoan_thanh' bi tu choi", False, "khong raise")
except Exception as e:  # pydantic.ValidationError
    check("LeadershipTaskReview.status='hoan_thanh' bi tu choi (422)",
          e.__class__.__name__ == "ValidationError", e.__class__.__name__)
try:
    LeadershipTaskCreate(commander_role="xyz", title="aaa", content="bbbbb")
    check("LeadershipTaskCreate.commander_role='xyz' bi tu choi", False, "khong raise")
except Exception as e:
    check("LeadershipTaskCreate.commander_role='xyz' bi tu choi (422)",
          e.__class__.__name__ == "ValidationError", e.__class__.__name__)

# F3: nop bao cao day trang thai sang da_bao_cao
task_flow = svc.create_task(db, lu_truong, LeadershipTaskCreate(
    commander_role="lu_truong", title="Luong trang thai chi dao", content="noi dung ddddd",
    target_branch="toan_lu_doan", urgency="thuong"))
check("chi dao moi tao -> dang_thuc_hien", task_flow.status == "dang_thuc_hien", task_flow.status)
after_report = svc.submit_report(db, canbo_d2, task_flow.id, rp)
check("sau submit_report -> da_bao_cao", after_report.status == "da_bao_cao", after_report.status)
after_review = svc.review_task(db, lu_truong, task_flow.id,
                               LeadershipTaskReview(status="can_bo_sung", review_note="bo sung so lieu"))
check("sau review 'can_bo_sung' -> can_bo_sung", after_review.status == "can_bo_sung", after_review.status)


print("\n== F4: pham vi xem danh sach / chi tiet chi dao ==")
# 'pham' (id=1) da la "Phòng Tham mưu" -> can bo don vi nay thuoc Khoi Tham muu
canbo_tm = mk("cb_tm", 4, pham.id)  # can bo Khoi Tham muu
# Chi dao pham vi rong theo khoi Tham muu (khong gan don vi)
task_tm_wide = svc.create_task(db, lu_truong, LeadershipTaskCreate(
    commander_role="lu_pho_tmt", title="Kiểm tra phiên liên lạc VTĐ toàn khối TM",
    content="Các đầu mối TTLL báo cáo chất lượng phiên liên lạc.", target_branch="tham_muu",
    assigned_unit_id=None, urgency="khan"))

# tong so chi dao trong DB: task_d1, task_all, task_flow, task_tm_wide = 4
all_ids = {task_d1.id, task_all.id, task_flow.id, task_tm_wide.id}


def ids(user):
    return {i.id for i in svc.list_tasks(db, user).items}


check("Lu truong (BCH) thay het 4 chi dao", ids(lu_truong) == all_ids, ids(lu_truong))
check("chi huy d1 (role 3) thay het 4 chi dao", ids(chi_huy_d1) == all_ids, ids(chi_huy_d1))
check("can bo d1 thay: task_d1 (don vi minh) + task rong; KHONG thay task khoi TM",
      ids(canbo_d1) == {task_d1.id, task_all.id, task_flow.id}, ids(canbo_d1))
check("can bo d2 KHONG thay task_d1 (giao cho d1); chi thay task rong toan LD",
      ids(canbo_d2) == {task_all.id, task_flow.id}, ids(canbo_d2))
check("can bo d2 KHONG thay task khoi Tham muu (khac khoi)",
      task_tm_wide.id not in ids(canbo_d2), ids(canbo_d2))
check("role 5 o d1 thay task_d1 (don vi minh) + task rong",
      ids(nguoi_dung) == {task_d1.id, task_all.id, task_flow.id}, ids(nguoi_dung))
check("can bo Khoi Tham muu thay task khoi TM + task rong toan LD; KHONG thay task_d1",
      ids(canbo_tm) == {task_tm_wide.id, task_all.id, task_flow.id}, ids(canbo_tm))
check("total khop so item tra ve (can bo d2)",
      svc.list_tasks(db, canbo_d2).total == len(svc.list_tasks(db, canbo_d2).items),
      svc.list_tasks(db, canbo_d2).total)

# get_task: ngoai pham vi -> 404
try:
    svc.get_task(db, canbo_d2, task_d1.id)
    check("get_task(can bo d2, task_d1) -> 404", False, "khong raise")
except HTTPException as e:
    check("get_task(can bo d2, task_d1) -> 404", e.status_code == 404, f"HTTP {e.status_code}")
expect_ok("get_task(can bo d1, task_d1) -> OK", lambda: svc.get_task(db, canbo_d1, task_d1.id))
expect_ok("get_task(can bo d2, task_all) -> OK", lambda: svc.get_task(db, canbo_d2, task_all.id))
expect_ok("get_task(Lu truong, task_d1) -> OK", lambda: svc.get_task(db, lu_truong, task_d1.id))

print()
if fails:
    print(f"KET QUA: {len(fails)} FAIL -> " + "; ".join(fails))
    sys.exit(1)
print("KET QUA: TAT CA PASS")
