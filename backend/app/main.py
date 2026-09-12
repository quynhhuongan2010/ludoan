from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import logging

from app.api.routes import (
    announcements,
    audit_logs,
    chats,
    command_threads,
    contacts,
    directive_assignments,
    directive_threads,
    directives,
    documents,
    duty_schedules,
    duty_shift_handovers,
    duty_week_plans,
    education_materials,
    home,
    items,
    leadership_tasks,
    official_dispatches,
    posts,
    profile,
    units,
    uploads,
    users,
)
from app.core.bootstrap import ensure_standard_units, ensure_system_admin
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models import (  # noqa: F401 -- register models for create_all
    announcement,
    audit_log,
    chat,
    command_thread,
    contact,
    directive,
    directive_assignment,
    directive_thread,
    document,
    duty_plan_attachment,
    duty_schedule,
    duty_shift_handover,
    duty_week_plan,
    education_material,
    leadership_task,
    official_dispatch,
    post,
    unit,
    user,
)

Base.metadata.create_all(bind=engine)
settings.upload_path.mkdir(parents=True, exist_ok=True)
settings.secure_upload_path.mkdir(parents=True, exist_ok=True)

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
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = next(
    (
        d.resolve()
        for d in (_REPO_ROOT / "fe-ludoan" / "dist", _REPO_ROOT / "frontend" / "dist")
        if (d / "index.html").is_file()
    ),
    (_REPO_ROOT / "fe-ludoan" / "dist").resolve(),
)

# Tang so nay moi lan thay doi hop dong API (them/sua/xoa endpoint hoac schema)
API_VERSION = "8.1.0"

app = FastAPI(
    title="Quynh Web API",
    version=API_VERSION,
    description="Cổng thông tin điện tử nội bộ Lữ đoàn Thông tin 21. Xem lịch sử thay đổi ở openapi.CHANGELOG.md.",
)

from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.rate_limit import api_rate_limiter


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware gioi han tan suat goi API theo IP de chong DoS mang noi bo."""
    path = request.url.path
    # Bo qua static files, docs va cac asset tinh
    if (
        path.startswith("/static")
        or path in ("/docs", "/redoc", "/openapi.json", "/favicon.ico")
        or path.endswith((".js", ".css", ".png", ".jpg", ".svg", ".woff2", ".ico"))
    ):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    is_allowed, remaining, retry_after = api_rate_limiter.check_request(client_ip)

    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": f"Quá nhiều yêu cầu từ địa chỉ IP này. Vui lòng thử lại sau {retry_after} giây để bảo đảm an toàn hệ thống."
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(settings.API_RATE_LIMIT_PER_MINUTE),
                "X-RateLimit-Remaining": "0",
            },
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(settings.API_RATE_LIMIT_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response

# CORS:
#  - localhost bat ky cong + dai IP LAN pho bien (10.x, 192.168.x, 172.16-31.x)
#  - cac domain tunnel hay dung khi CHIA SE TAM qua 1 link duy nhat: ngrok
#    (*.ngrok-free.app / *.ngrok-free.dev / *.ngrok.io / *.ngrok.app / *.ngrok.dev),
#    cloudflared (*.trycloudflare.com), localtunnel (*.loca.lt).
#  - EXTRA_CORS_ORIGINS trong .env: them domain co dinh khac (ngrok tra phi...).
#  - CORS_ALLOW_ALL_ORIGINS=true trong .env: phan chieu MOI origin (chi trinh dien).
# Luu y: cach chia se GON NHAT (khong dung CORS) van la build Frontend roi de
# Backend phuc vu luon -> tunnel DUY NHAT cong 8000, Frontend goi API tuong doi
# nen luon cung origin. Xem .env.production cua fe-ludoan (de VITE_API_BASE_URL rong).
if settings.CORS_ALLOW_ALL_ORIGINS:
    _cors_origin_regex = r".*"
else:
    _cors_origin_regex = (
        r"^https?://("
        r"localhost|127\.0\.0\.1|\[::1\]"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
        r"|(?:[a-z0-9-]+\.)+ngrok-free\.app"
        r"|(?:[a-z0-9-]+\.)+ngrok-free\.dev"
        r"|(?:[a-z0-9-]+\.)+ngrok\.io"
        r"|(?:[a-z0-9-]+\.)+ngrok\.app"
        r"|(?:[a-z0-9-]+\.)+ngrok\.dev"
        r"|(?:[a-z0-9-]+\.)+trycloudflare\.com"
        r"|(?:[a-z0-9-]+\.)+loca\.lt"
        r")(:\d+)?$"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.extra_cors_list,
    allow_origin_regex=_cors_origin_regex,
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
app.include_router(chats.router)
app.include_router(chats.ws_router)  # kenh WebSocket thoi gian thuc /chats/ws
app.include_router(official_dispatches.router)
app.include_router(announcements.router)
app.include_router(duty_schedules.router)
app.include_router(duty_week_plans.router)
app.include_router(duty_shift_handovers.router)
app.include_router(leadership_tasks.router)
app.include_router(documents.router)
app.include_router(contacts.router)
app.include_router(home.router)
app.include_router(uploads.router)
app.include_router(audit_logs.router)


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
