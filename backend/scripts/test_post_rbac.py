"""Kiem thu logic phan quyen + bac phan loai cho post_service.list_posts.

Chay tu thu muc backend/:
    ./venv/Scripts/python.exe ../<scratchpad>/test_post_rbac.py

Dung SQLite in-memory - KHONG dung toi MySQL that.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # fallback
# duong dan backend/ (script nam ngoai, truyen qua argv hoac cwd)
BACKEND = pathlib.Path.cwd()
sys.path.insert(0, str(BACKEND))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models.unit, app.models.user, app.models.post  # noqa
from app.models.user import User
from app.models.post import Post
from app.core.security import hash_password
from app.services import post_service
from fastapi import HTTPException

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
S = sessionmaker(bind=engine)
db = S()

def mk_user(uname, role, clearance=False):
    u = User(username=uname, hashed_password=hash_password("x"), full_name=uname.upper(),
             role=role, is_active=True, clearance=clearance)
    db.add(u); db.commit(); db.refresh(u); return u

commander = mk_user("cmd", "commander")
officer   = mk_user("off", "officer")
officer2  = mk_user("off2", "officer")
soldier   = mk_user("sol", "soldier")
cleared   = mk_user("clr", "soldier", clearance=True)

def mk_post(title, author, status, classification):
    p = Post(title=title, category="huan_luyen", content="...",
             status=status, classification=classification, author_id=author.id)
    db.add(p); db.commit(); db.refresh(p); return p

mk_post("CK-duyet",      officer,  "da_duyet",  "cong_khai")
mk_post("NB-duyet",      officer,  "da_duyet",  "noi_bo")
mk_post("MAT-duyet",     commander,"da_duyet",  "mat")
mk_post("NB-choduyet",   officer,  "cho_duyet", "noi_bo")
mk_post("NB-choduyet-2", officer2, "cho_duyet", "noi_bo")

def titles(rows): return sorted(r.title for r in rows)
fails = []
def check(label, got, want):
    ok = got == want
    print(("PASS" if ok else "FAIL"), label, "->", got, "" if ok else f"(want {want})")
    if not ok: fails.append(label)

# --- khach (chua dang nhap): chi cong_khai + da_duyet
check("guest", titles(post_service.list_posts(db, None)), ["CK-duyet"])
# --- soldier: cong_khai + noi_bo, chi da_duyet
check("soldier", titles(post_service.list_posts(db, soldier)), ["CK-duyet", "NB-duyet"])
# --- soldier co clearance: thay them MAT
check("cleared", titles(post_service.list_posts(db, cleared)), ["CK-duyet", "MAT-duyet", "NB-duyet"])
# --- officer: feed da_duyet (theo bac) + moi bai cua chinh minh
check("officer", titles(post_service.list_posts(db, officer)),
      sorted(["CK-duyet", "NB-duyet", "NB-choduyet"]))
# officer KHONG thay bai cho_duyet cua officer2
check("officer-not-others-draft",
      "NB-choduyet-2" in titles(post_service.list_posts(db, officer)), False)
# --- commander: thay tat ca
check("commander-all", titles(post_service.list_posts(db, commander)),
      sorted(["CK-duyet", "NB-duyet", "MAT-duyet", "NB-choduyet", "NB-choduyet-2"]))

# --- BO LOC classification moi ---
check("guest+filter=noi_bo (khong duoc xem -> rong)",
      titles(post_service.list_posts(db, None, classification="noi_bo")), [])
check("soldier+filter=cong_khai",
      titles(post_service.list_posts(db, soldier, classification="cong_khai")), ["CK-duyet"])
check("soldier+filter=mat (khong du quyen -> rong)",
      titles(post_service.list_posts(db, soldier, classification="mat")), [])
check("cleared+filter=mat",
      titles(post_service.list_posts(db, cleared, classification="mat")), ["MAT-duyet"])
check("commander+filter=noi_bo",
      titles(post_service.list_posts(db, commander, classification="noi_bo")),
      sorted(["NB-duyet", "NB-choduyet", "NB-choduyet-2"]))
check("commander+filter=cong_khai",
      titles(post_service.list_posts(db, commander, classification="cong_khai")), ["CK-duyet"])

# --- classification khong hop le -> 422
try:
    post_service.list_posts(db, commander, classification="xyz")
    check("invalid-classification-raises-422", "no raise", "HTTPException 422")
except HTTPException as e:
    check("invalid-classification-raises-422", e.status_code, 422)

# --- guard tao noi dung mat (403) ---
from app.schemas.post import PostCreate
try:
    post_service.create_post(db, PostCreate(title="x", category="huan_luyen", content="c",
                                            classification="mat"), soldier)
    check("soldier-create-mat-403", "no raise", "HTTPException 403")
except HTTPException as e:
    check("soldier-create-mat-403", e.status_code, 403)

# officer co clearance tao duoc bai mat, va vao hang cho_duyet
p = post_service.create_post(db, PostCreate(title="mat-by-cleared", category="huan_luyen",
                                            content="c", classification="mat"), cleared)
check("cleared-create-mat-status", p.status, "cho_duyet")

print()
print("KET QUA:", "TAT CA PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
