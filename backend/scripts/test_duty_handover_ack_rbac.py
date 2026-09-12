"""Kiem thu phan quyen + guard trang thai cho POST /duty-shift-handovers/{id}/acknowledge
(Vong 2 - F7).

Truoc khi va: bat ky tai khoan da kich hoat nao cung "ky nhan" duoc moi bien ban,
chiem receiver_id, va ky lai ca sau khi chi huy da duyet.

Sau khi va (`duty_shift_handover_service`):
  - Chi ky nhan khi status == "cho_nhan"           -> 409 neu da ky
  - Nguoi lap bien ban khong tu ky nhan             -> 403
  - Bien ban da chi dinh nguoi nhan: chi dung nguoi -> 403 voi nguoi khac
  - Bien ban chua chi dinh: role 5 khong ky nhan    -> 403
  - Ban Chi huy (role 0..3): luon ky nhan duoc
  - create_handover: role 5 khong lap bien ban      -> 403; tu ban giao cho minh -> 400

Dung SQLite in-memory. Chay tu backend/:
    venv/Scripts/python.exe scripts/test_duty_handover_ack_rbac.py
"""

import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path.cwd()))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models  # noqa: F401  (dang ky toan bo mapper)
from app.models.unit import Unit
from app.models.user import User
from app.models.duty_week_plan import DutyWeekPlan
from app.models.duty_schedule import DutySchedule
from app.schemas.duty_shift_handover import (
    DutyShiftHandoverAcknowledge,
    DutyShiftHandoverCreate,
)
from app.services import duty_shift_handover_service as svc

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
db = sessionmaker(bind=engine)()

fails: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + label + (f"  -> {detail}" if detail else ""))
    if not cond:
        fails.append(label)


def expect_status(label: str, fn, code: int) -> None:
    try:
        fn()
        check(label, False, f"khong raise (mong doi {code})")
    except HTTPException as e:
        check(label, e.status_code == code, f"HTTP {e.status_code}: {e.detail}")


def expect_ok(label: str, fn):
    try:
        return fn(), check(label, True)
    except HTTPException as e:
        check(label, False, f"HTTP {e.status_code}: {e.detail}")


d1 = Unit(id=1, name="Tiểu đoàn 1", unit_kind="tieu_doan")
db.add(d1)
db.commit()


def mk(uname, role):
    u = User(username=uname, hashed_password="h", full_name=uname.upper(),
             role=role, is_active=True, unit_id=1)
    db.add(u); db.commit(); db.refresh(u); return u


giver = mk("giver", 4)          # can bo lap bien ban
receiver = mk("receiver", 4)    # can bo duoc chi dinh nhan
other_cb = mk("other_cb", 4)    # can bo khac
nguoi_dung = mk("nd", 5)        # role 5 chi xem
chi_huy = mk("ch", 2)           # Ban Chi huy

plan = DutyWeekPlan(id=1, unit_id=1, week_start=date(2026, 9, 7), status="da_duyet", author_id=giver.id)
db.add(plan); db.commit()


def mk_schedule(sid: int) -> DutySchedule:
    s = DutySchedule(id=sid, week_plan_id=1, unit_id=1, duty_date=date(2026, 9, 8),
                     duty_type="truc_ban_noi_vu", shift="Ngày", duty_officer="Trực ban",
                     role_title="Trực ban nội vụ", author_id=giver.id)
    db.add(s); db.commit(); db.refresh(s); return s


mk_schedule(1); mk_schedule(2); mk_schedule(3)

ack = DutyShiftHandoverAcknowledge(status="da_nhan", receiver_note="Đã đối chiếu, nhận đủ.")

print("\n== F7: create_handover guard ==")
expect_status("role 5 lap bien ban ban giao -> 403", lambda: svc.create_handover(
    db, nguoi_dung, DutyShiftHandoverCreate(schedule_id=1)), 403)
expect_status("tu ban giao ca cho chinh minh -> 400", lambda: svc.create_handover(
    db, giver, DutyShiftHandoverCreate(schedule_id=1, receiver_id=giver.id)), 400)

# bien ban 1: co chi dinh receiver
h1 = svc.create_handover(db, giver, DutyShiftHandoverCreate(schedule_id=1, receiver_id=receiver.id))
# bien ban 2: KHONG chi dinh receiver
h2 = svc.create_handover(db, giver, DutyShiftHandoverCreate(schedule_id=2))

print("\n== F7: acknowledge_handover phan quyen ==")
expect_status("nguoi lap tu ky nhan bien ban cua minh -> 403",
              lambda: svc.acknowledge_handover(db, giver, h1.id, ack), 403)
expect_status("can bo khac ky nhan bien ban da chi dinh nguoi khac -> 403",
              lambda: svc.acknowledge_handover(db, other_cb, h1.id, ack), 403)
expect_status("role 5 ky nhan bien ban chua chi dinh nguoi nhan -> 403",
              lambda: svc.acknowledge_handover(db, nguoi_dung, h2.id, ack), 403)
expect_ok("dung nguoi nhan duoc chi dinh ky nhan -> OK",
          lambda: svc.acknowledge_handover(db, receiver, h1.id, ack))
expect_status("ky nhan lai bien ban da 'da_nhan' -> 409",
              lambda: svc.acknowledge_handover(db, receiver, h1.id, ack), 409)
expect_status("chi huy ky nhan lai bien ban da chot -> 409 (guard trang thai truoc quyen)",
              lambda: svc.acknowledge_handover(db, chi_huy, h1.id, ack), 409)
expect_ok("Ban Chi huy ky nhan bien ban chua chi dinh nguoi nhan -> OK",
          lambda: svc.acknowledge_handover(db, chi_huy, h2.id, ack))

# bien ban 3: chua chi dinh -> can bo bat ky trong bien che duoc ky
h3 = svc.create_handover(db, giver, DutyShiftHandoverCreate(schedule_id=3))
expect_ok("can bo (role 4) ky nhan bien ban chua chi dinh nguoi nhan -> OK",
          lambda: svc.acknowledge_handover(db, other_cb, h3.id, ack))

print()
if fails:
    print(f"KET QUA: {len(fails)} FAIL -> " + "; ".join(fails))
    sys.exit(1)
print("KET QUA: TAT CA PASS")
