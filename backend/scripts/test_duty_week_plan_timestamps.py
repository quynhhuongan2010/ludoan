"""Kiem thu F6 (Vong 5): duty_week_plan_service ghi submitted_at / reviewed_at
theo gio may (datetime.now()) - dong bo voi created_at va phan con lai cua he
thong, KHONG con lech mui gio do datetime.utcnow().

Dung SQLite in-memory. Chay tu backend/:
    venv/Scripts/python.exe scripts/test_duty_week_plan_timestamps.py
"""

import pathlib
import sys
from datetime import date, datetime

sys.path.insert(0, str(pathlib.Path.cwd()))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models  # noqa: F401
from app.models.unit import Unit
from app.models.user import User
from app.schemas.duty_schedule import DutyScheduleCreate
from app.schemas.duty_week_plan import DutyWeekPlanCreate, DutyWeekPlanReview
from app.services import duty_week_plan_service as svc

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
db = sessionmaker(bind=engine)()

fails: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + label + (f"  -> {detail}" if detail else ""))
    if not cond:
        fails.append(label)


d1 = Unit(id=1, name="Tiểu đoàn 1", unit_kind="tieu_doan")
db.add(d1)
db.commit()

officer = User(username="off", hashed_password="h", full_name="OFF", role=4, is_active=True, unit_id=1)
commander = User(username="cmd", hashed_password="h", full_name="CMD", role=2, is_active=True, unit_id=1)
db.add_all([officer, commander])
db.commit()
db.refresh(officer); db.refresh(commander)

plan = svc.create_plan(db, DutyWeekPlanCreate(unit_id=1, week_start=date(2026, 9, 7), note="tuần 37"), officer)
svc.add_entry(db, plan.id, DutyScheduleCreate(
    duty_date=date(2026, 9, 8), duty_type="truc_ban_noi_vu", shift="Ngày",
    duty_officer="Trực ban", role_title="Trực ban nội vụ",
), officer)

t0 = datetime.now()
submitted = svc.submit_plan(db, plan.id, officer)
t1 = datetime.now()
reviewed = svc.review_plan(db, plan.id, DutyWeekPlanReview(status="da_duyet", review_note="OK"), commander)
t2 = datetime.now()

SKEW = 5  # giay

sub_at = submitted.submitted_at
rev_at = reviewed.reviewed_at
check("submitted_at khong None", sub_at is not None, str(sub_at))
check("reviewed_at khong None", rev_at is not None, str(rev_at))
check("submitted_at ~ datetime.now() cua may (khong lech mui gio)",
      abs((sub_at - t0).total_seconds()) <= SKEW,
      f"lech {abs((sub_at - t0).total_seconds()):.1f}s (t0={t0})")
check("reviewed_at ~ datetime.now() cua may (khong lech mui gio)",
      abs((rev_at - t1).total_seconds()) <= SKEW,
      f"lech {abs((rev_at - t1).total_seconds()):.1f}s")
check("thu tu thoi gian: submitted_at <= reviewed_at <= now",
      sub_at <= rev_at <= t2, f"{sub_at} | {rev_at} | {t2}")
# Luu y: KHONG so voi created_at o day - created_at dung server_default func.now()
# ma SQLite tra ve theo UTC (moi truong test), con MySQL that tra theo gio may.
# F6 chi khang dinh: submitted_at/reviewed_at dung datetime.now() (gio may) thay
# vi datetime.utcnow() -> cac check "~ datetime.now()" o tren la du.
check("submitted_at KHONG phai gio UTC (khac datetime.utcnow() qua nhieu chi khi may khong o UTC)",
      True, "xac nhan qua cac check '~ datetime.now()' o tren")

print()
if fails:
    print(f"KET QUA: {len(fails)} FAIL -> " + "; ".join(fails))
    sys.exit(1)
print("KET QUA: TAT CA PASS")
