from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import logging

from app.api.routes import (
    announcements,
    command_meetings,
    command_threads,
    directive_assignments,
    directive_threads,
    directives,
    documents,
    duty_schedules,
    education_materials,
    home,
    items,
    official_dispatches,
    posts,
    profile,
    units,
    users,
)
from app.core.bootstrap import ensure_standard_units, ensure_system_admin
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models import (  # noqa: F401 -- register models for create_all
    announcement,
    command_meeting,
    command_thread,
    directive,
    directive_assignment,
    directive_thread,
    document,
    duty_schedule,
    education_material,
    official_dispatch,
    post,
    unit,
    user,
)

Base.metadata.create_all(bind=engine)
settings.upload_path.mkdir(parents=True, exist_ok=True)

# Seed tai khoan admin he thong (bo qua loi neu DB cu chua chay migration)
try:
    with SessionLocal() as _db:
        ensure_system_admin(_db)
except Exception:  # noqa: BLE001
    logging.getLogger(__name__).exception("Khong the khoi tao tai khoan admin he thong")

# Seed co cau to chuc chuan CHI khi bang units con rong (cai dat moi).
# De khong "hoi sinh" don vi da bi xoa, chi seed luc dau. Bo sung sau: chay tay
# scripts/seed_units.py.
try:
    from app.models.unit import Unit as _Unit

    with SessionLocal() as _db:
        if _db.query(_Unit).count() == 0:
            ensure_standard_units(_db)
except Exception:  # noqa: BLE001
    logging.getLogger(__name__).exception("Khong the khoi tao co cau don vi chuan")

# Thu muc ban build tinh cua Frontend (ket qua `npm run build` -> frontend/dist).
# Khi co mat, Backend tu phuc vu luon Frontend qua cung 1 cong duy nhat (xem
# phan "Phuc vu Frontend tinh (SPA)" o cuoi file) -> trien khai san xuat chi
# can chay 1 tien trinh (uvicorn), khong can may chu web rieng cho giao dien.
FRONTEND_DIST = (Path(__file__).resolve().parent.parent.parent / "frontend" / "dist").resolve()

# Tang so nay moi lan thay doi hop dong API (them/sua/xoa endpoint hoac schema)
API_VERSION = "1.9.1"

app = FastAPI(
    title="Quynh Web API",
    version=API_VERSION,
    description="Cổng thông tin điện tử nội bộ Lữ đoàn Thông tin 21. Xem lịch sử thay đổi ở openapi.CHANGELOG.md.",
)

# CORS: cho phep localhost bat ky cong + dai IP LAN pho bien (10.x, 192.168.x, 172.16-31.x)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.extra_cors_list,
    allow_origin_regex=(
        r"^https?://("
        r"localhost|127\.0\.0\.1|\[::1\]"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
        r")(:\d+)?$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(settings.upload_path)), name="static")


@app.get("/", tags=["root"])
def read_root():
    # Trien khai san xuat (da build Frontend): tra ve luon giao dien SPA.
    # Che do API-only (chua build Frontend, vd moi trinh + npm run dev rieng
    # o cong 5173): giu nguyen JSON thong tin nhu truoc.
    index_file = FRONTEND_DIST / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {
        "name": "Quynh Web API",
        "status": "ok",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


app.include_router(items.router)
app.include_router(units.router)
app.include_router(users.router)
app.include_router(profile.router)
app.include_router(posts.router)
app.include_router(education_materials.router)
app.include_router(directives.router)
app.include_router(directive_threads.router)
app.include_router(directive_assignments.router)
app.include_router(command_threads.router)
app.include_router(official_dispatches.router)
app.include_router(command_meetings.router)
app.include_router(announcements.router)
app.include_router(duty_schedules.router)
app.include_router(documents.router)
app.include_router(home.router)


# ---------------------------------------------------------------------------
# Phuc vu Frontend tinh (SPA) - toan bo he thong chay tren 1 cong duy nhat.
# Dat SAU CUNG (sau moi app.include_router o tren) de KHONG che bat ky route
# API nao: FastAPI/Starlette khop route theo thu tu dang ky, nen cac duong
# dan API (vd /users, /posts, /directives...) da dang ky truoc luon duoc uu
# tien; chi nhung duong dan KHONG khop router nao (cac route dieu huong phia
# client cua React Router nhu /bang-tin, /tin-tuc, /chi-thi-nhiem-vu...) moi
# roi xuong day va duoc tra ve index.html de SPA tu xu ly.
#
# Luu y: trang /items (demo CRUD noi bo, khong thuoc sitemap nghiep vu) trung
# duong dan voi API GET /items nen khi F5 truc tiep tren duong dan nay se
# nhan JSON tu API thay vi giao dien - dieu huong tu ben trong ung dung (React
# Router) van hoat dong binh thuong.
if FRONTEND_DIST.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="frontend-assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_spa(full_path: str):
        # Neu la file tinh co that trong frontend/dist (vd favicon.svg,
        # icons.svg) thi phuc vu truc tiep; con lai (moi route dieu huong
        # cua SPA) tra ve index.html. .resolve() + kiem tra parents chan
        # duyet thu muc ra ngoai (path traversal qua "..").
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.is_file() and FRONTEND_DIST in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
