"""Kiem thu F5 (Vong 4): POST /chats/{id}/members phai kiem tra user ton tai/active.

Truoc khi va: them user_id bat ky -> sinh ChatParticipant mo coi.
Sau khi va: user_id khong ton tai / da bi khoa -> 404, khong tao participant.

Dung SQLite in-memory. Chay tu backend/:
    venv/Scripts/python.exe scripts/test_chat_add_member_validation.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.cwd()))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models  # noqa: F401
from app.models.chat import ChatParticipant
from app.models.user import User
from app.schemas.chat import ChatAddMemberPayload, GroupChatCreate
from app.services import chat_service as svc

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
db = sessionmaker(bind=engine)()

fails: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + label + (f"  -> {detail}" if detail else ""))
    if not cond:
        fails.append(label)


def mk(uname, role, active=True):
    u = User(username=uname, hashed_password="h", full_name=uname.upper(),
             role=role, is_active=active)
    db.add(u); db.commit(); db.refresh(u); return u


owner = mk("owner", 2)  # Ban Chi huy -> nhom tao ra la "da_duyet" dung ngay
member = mk("member", 4)
locked = mk("locked", 4, active=False)

grp = svc.create_group_chat(db, owner, GroupChatCreate(name="Kíp trực 1", member_ids=[]))


def add(uid: int):
    return svc.add_member_to_group(db, owner, grp.id, uid)


def expect_404(label, uid):
    try:
        add(uid)
        check(label, False, "khong raise (mong doi 404)")
    except HTTPException as e:
        check(label, e.status_code == 404, f"HTTP {e.status_code}: {e.detail}")


expect_404("them user_id khong ton tai (99999) -> 404", 99999)
expect_404("them tai khoan da bi khoa -> 404", locked.id)

before = db.query(ChatParticipant).filter(ChatParticipant.conversation_id == grp.id).count()
try:
    add(member.id)
    check("them tai khoan hop le -> OK", True)
except HTTPException as e:
    check("them tai khoan hop le -> OK", False, f"HTTP {e.status_code}: {e.detail}")
after = db.query(ChatParticipant).filter(ChatParticipant.conversation_id == grp.id).count()
check("chi tang dung 1 participant (khong sinh ban ghi mo coi)", after == before + 1, f"{before} -> {after}")

orphans = (
    db.query(ChatParticipant)
    .outerjoin(User, User.id == ChatParticipant.user_id)
    .filter(User.id.is_(None))
    .count()
)
check("khong con ChatParticipant mo coi trong DB", orphans == 0, f"orphans={orphans}")

print()
if fails:
    print(f"KET QUA: {len(fails)} FAIL -> " + "; ".join(fails))
    sys.exit(1)
print("KET QUA: TAT CA PASS")
