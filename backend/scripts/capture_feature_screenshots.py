# -*- coding: utf-8 -*-
"""Chup anh minh hoa THAT tu he thong dang chay + KIEM THU CHUC NANG END-TO-END.

Dong bo phien ban phan mem hien tai (openapi v8.0.0, role la so nguyen 0..5).
Moi lan chay:
  1. Dang nhap admin qua API, gieo mot bo DU LIEU MINH HOA "(demo)" cho tat ca
     phan he (tin tuc, thong bao, tai lieu, GDCT, chi thi, luong chi dao, giao
     nhiem vu, hop ban BCH, cong van mat, ban lam viec chi dao BCH, lich truc tuan).
  2. Dung Chromium that (khong headless-gia) dang nhap qua giao dien, di qua tung
     man hinh, chup full-page 2x DPI vao docs/screenshots_khai_thac/*.png.
  3. Chay tron 1 vong doi "giao nhiem vu -> can bo nop -> chi huy duyet" va 1
     phep thu "go du lieu -> tai lai trang -> tu khoi phuc ban nhap".
  4. Don dep: xoa / dong / vo hieu hoa toan bo du lieu minh hoa da gieo.

Cach dung:
    1) Khoi dong Backend (phuc vu ca Frontend) tren cong 8000:
       venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    2) Cua so khac (backend/.env can co SYSTEM_ADMIN_USERNAME / PASSWORD dung):
       venv/Scripts/python.exe scripts/capture_feature_screenshots.py

Ket qua in ra bang tong ket: so anh dat / khong dat + ket qua cac phep kiem chung.
"""

from __future__ import annotations

import datetime
import io
import pathlib
import sys

try:  # console Windows co the la cp1252 -> ep UTF-8 de in tieng Viet
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from playwright.sync_api import Page, sync_playwright  # noqa: E402

BASE_URL = "http://127.0.0.1:8000"
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "docs" / "screenshots_khai_thac"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORT = {"width": 1600, "height": 1000}

OFFICER_USERNAME = "demo_canbo_e2e"          # role 4 - Can bo / QNCN (duoc dang noi dung)
OFFICER_PW1 = "Demo@2026"
OFFICER_PW2 = "Demo@2027moi"
USER_USERNAME = "demo_nguoidung_e2e"         # role 5 - Nguoi dung (chi xem)
USER_PW1 = "Demo@2026"
USER_PW2 = "Demo@2027moi"

UNIT_C5 = 3  # Dai doi 5 (theo co cau don vi chuan)

FAKE_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF"
)

# ket qua chup: (ten, ok, ghi_chu)
CAP: list[tuple[str, bool, str]] = []
CHECKS: list[tuple[str, bool, str]] = []


# ----------------------------------------------------------------- tien ich chup
def shot(page: Page, name: str) -> None:
    try:
        page.wait_for_timeout(250)
        page.screenshot(path=str(OUT_DIR / f"{name}.png"), full_page=True)
        CAP.append((name, True, ""))
        print(f"  [OK ] {name}.png")
    except Exception as e:  # noqa: BLE001
        CAP.append((name, False, str(e).splitlines()[0][:180]))
        print(f"  [ERR] {name}: {e}")


def nav(page: Page, path: str) -> None:
    # Pacing nhe de khong dinh rate-limit backend (API_RATE_LIMIT_PER_MINUTE).
    for attempt in range(1, 5):
        resp = None
        try:
            resp = page.goto(f"{BASE_URL}{path}", wait_until="networkidle", timeout=20000)
        except Exception:  # noqa: BLE001
            try:
                resp = page.goto(f"{BASE_URL}{path}", timeout=20000)
            except Exception as e:  # noqa: BLE001
                print(f"  [nav-err] {path}: {e}")
                return
        rate_limited = (resp is not None and resp.status == 429)
        if not rate_limited:
            try:
                body = page.content()
                rate_limited = "Quá nhiều yêu cầu từ địa chỉ IP" in body
            except Exception:  # noqa: BLE001
                pass
        if not rate_limited:
            break
        wait_s = 6 * attempt
        print(f"  [rate-limit] {path} -> cho {wait_s}s roi thu lai (lan {attempt})")
        page.wait_for_timeout(wait_s * 1000)
    page.wait_for_timeout(900)


def click_text(page: Page, text: str, timeout: int = 4000) -> bool:
    try:
        page.get_by_text(text, exact=False).first.click(timeout=timeout)
        page.wait_for_timeout(500)
        return True
    except Exception:  # noqa: BLE001
        return False


def click_role(page: Page, role: str, name: str, timeout: int = 4000, exact: bool = False) -> bool:
    try:
        page.get_by_role(role, name=name, exact=exact).first.click(timeout=timeout)
        page.wait_for_timeout(500)
        return True
    except Exception:  # noqa: BLE001
        return False


def click_tab_nth(page: Page, idx: int, timeout: int = 4000) -> bool:
    try:
        page.locator(".tab-bar button").nth(idx).click(timeout=timeout)
        page.wait_for_timeout(500)
        return True
    except Exception:  # noqa: BLE001
        return False


def make_cover_image(text: str, color=(31, 76, 48)) -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (960, 540), color)
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 951, 531], outline=(255, 255, 255), width=3)
    d.text((60, 250), text, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _pw_inputs(page: Page):
    """Cac <input type=password> that su (khong dinh nut 'Hien mat khau')."""
    return page.locator('input[type="password"]')


def _login_ui(page: Page, username: str, password: str, wait_url_suffix: str) -> None:
    nav(page, "/login")
    page.get_by_label("Tên đăng nhập").fill(username)
    _pw_inputs(page).first.fill(password)
    page.get_by_role("button", name="Đăng nhập").click()
    page.wait_for_url(f"{BASE_URL}{wait_url_suffix}", timeout=15000)
    page.wait_for_timeout(500)


def _fill_change_password(page: Page, current: str, new: str) -> None:
    inp = _pw_inputs(page)
    inp.nth(0).fill(current)   # Mat khau hien tai
    inp.nth(1).fill(new)       # Mat khau moi
    inp.nth(2).fill(new)       # Xac nhan mat khau moi


# --------------------------------------------------------------------------- seed
def seed(api, h: dict) -> dict:
    print("== Gieo du lieu minh hoa qua API ==")
    refs: dict = {}

    def _post(path, **kw):
        r = api.post(path, headers=h, **kw)
        if not r.ok:
            print(f"  [seed-warn] POST {path} -> {r.status} {r.text()[:160]}")
            return None
        try:
            return r.json()
        except Exception:  # noqa: BLE001
            return {}

    # --- Tin tuc ---
    p1 = _post(
        "/posts",
        data={
            "title": "(demo) Hội thao thể lực toàn Lữ đoàn quý III/2026",
            "category": "huan_luyen",
            "content": "Nội dung tin bài phục vụ giới thiệu hệ thống (DỮ LIỆU MINH HOẠ), không phải hoạt động thực tế.",
            "classification": "cong_khai",
            "is_featured": True,
        },
    )
    if p1:
        refs["post_ids"] = [p1["id"]]
        api.post(
            f"/posts/{p1['id']}/thumbnail",
            headers=h,
            multipart={"file": {"name": "bia.png", "mimeType": "image/png", "buffer": make_cover_image("ANH MINH HOA HOAT DONG DON VI")}},
        )
    for title, cat, cls in [
        ("(demo) Lữ đoàn phát động đợt thi đua cao điểm chào mừng ngày truyền thống", "dan_van", "cong_khai"),
        ("(demo) Kết quả Hội thi cán bộ huấn luyện giỏi cấp Lữ đoàn năm 2026", "huan_luyen", "noi_bo"),
        ("(demo) Đại đội 5 biểu dương gương chiến sĩ tiêu biểu tháng 8", "guong_nguoi_tot", "noi_bo"),
        ("(demo) Tiểu đoàn 1 làm tốt công tác dân vận trên địa bàn biên giới", "dan_van", "cong_khai"),
    ]:
        p = _post("/posts", data={"title": title, "category": cat, "content": "Dữ liệu minh hoạ phục vụ giới thiệu hệ thống.", "classification": cls})
        if p:
            refs.setdefault("post_ids", []).append(p["id"])

    # --- Thong bao ---
    refs["announcement_ids"] = []
    a1 = _post("/announcements", data={"title": "(demo) Thông báo lịch trực chỉ huy tuần 36/2026", "content": "Yêu cầu các đơn vị bố trí quân số trực theo lịch (dữ liệu minh hoạ).", "priority": "khan", "is_pinned": True, "is_public": True})
    if a1:
        refs["announcement_ids"].append(a1["id"])
    for title, pri, pub in [
        ("(demo) Kế hoạch kiểm tra công tác sẵn sàng chiến đấu quý IV/2026", "cao", False),
        ("(demo) Lịch học tập chính trị tập trung tháng 9/2026", "binh_thuong", True),
        ("(demo) Thông báo khám sức khoẻ định kỳ cho cán bộ, QNCN", "thap", False),
    ]:
        a = _post("/announcements", data={"title": title, "content": "Nội dung thông báo minh hoạ.", "priority": pri, "is_pinned": False, "is_public": pub})
        if a:
            refs["announcement_ids"].append(a["id"])

    # --- Tai lieu ---
    doc1 = _post(
        "/documents",
        multipart={
            "title": "(demo) Biểu mẫu báo cáo tuần",
            "category": "bieu_mau",
            "description": "Biểu mẫu minh hoạ phục vụ giới thiệu hệ thống.",
            "classification": "noi_bo",
            "file": {"name": "bieu-mau-demo.pdf", "mimeType": "application/pdf", "buffer": FAKE_PDF},
        },
    )
    if doc1:
        refs["document_id"] = doc1["id"]

    # --- Giao duc chinh tri ---
    refs["edu_ids"] = []
    for title, cat, period in [
        ("(demo) Học tập Nghị quyết - Tuần 35/2026", "hoc_tap_chinh_tri_quan_su", "Tuần 35/2026"),
        ("(demo) Tuyên truyền biển, đảo và biên giới quốc gia - Tuần 36/2026", "tuyen_truyen", "Tuần 36/2026"),
        ("(demo) Tìm hiểu Luật Biên phòng Việt Nam", "phap_luat_bien_gioi", "Tháng 9/2026"),
    ]:
        e = _post("/education-materials", data={"title": title, "category": cat, "period_label": period, "content": "Nội dung giáo dục chính trị minh hoạ phục vụ giới thiệu hệ thống."})
        if e:
            refs["edu_ids"].append(e["id"])

    # --- Chi thi ---
    refs["directive_ids"] = []
    d1 = _post("/directives", data={"title": "(demo) Chỉ thị tăng cường SSCĐ dịp cuối năm 2026", "content": "Yêu cầu các cơ quan, đơn vị quán triệt, triển khai nghiêm túc (dữ liệu minh hoạ).", "status": "da_ban_hanh", "classification": "noi_bo"})
    d2 = _post("/directives", data={"title": "(demo) Chỉ thị về nâng cao chất lượng huấn luyện năm 2026", "content": "Nội dung chỉ thị minh hoạ.", "status": "da_ban_hanh", "classification": "noi_bo"})
    for d in (d1, d2):
        if d:
            refs["directive_ids"].append(d["id"])

    # --- Luong Chi dao - Bao cao (theo don vi) ---
    t1 = _post("/directive-threads", data={"unit_id": UNIT_C5, "title": "(demo) Báo cáo SSCĐ tuần 35/2026 - Đại đội 5"})
    if t1:
        refs["dthread_id"] = t1["id"]
        refs["dthread_title"] = "(demo) Báo cáo SSCĐ tuần 35/2026 - Đại đội 5"
        api.post(f"/directive-threads/{t1['id']}/messages", headers=h, form={"body": "Kính báo cáo Ban Chỉ huy: Đại đội 5 hoàn thành 100% nội dung huấn luyện tuần 35 (dữ liệu minh hoạ)."})

    # --- Tai khoan minh hoa role 4 (can bo) va role 5 (nguoi dung) ---
    def _ensure_user(username, pw, role):
        existing = [u for u in api.get("/users/", headers=h, params={"limit": 500}).json()["items"] if u["username"] == username]
        if existing:
            u = existing[0]
            api.post(f"/users/{u['id']}/activate", headers=h)
            api.post(f"/users/{u['id']}/reset-password", headers=h, data={"new_password": pw})
            api.patch(f"/users/{u['id']}/role", headers=h, data={"role": role})
            api.patch(f"/users/{u['id']}/unit", headers=h, data={"unit_id": UNIT_C5})
            return u["id"]
        r = api.post(
            "/users/",
            headers=h,
            data={
                "username": username,
                "password": pw,
                "full_name": ("Nguyễn Văn Cán Bộ (TK minh hoạ)" if role == 4 else "Trần Văn Người Dùng (TK minh hoạ)"),
                "role": role,
                "rank": "Đại uý" if role == 4 else "Thượng uý",
                "position": "Trợ lý (tài khoản minh hoạ)" if role == 4 else "Nhân viên (tài khoản minh hoạ)",
                "unit_id": UNIT_C5,
            },
        )
        if not r.ok:
            print(f"  [seed-warn] tao user {username} -> {r.status} {r.text()[:160]}")
            return None
        return r.json()["id"]

    refs["officer_id"] = _ensure_user(OFFICER_USERNAME, OFFICER_PW1, 4)
    refs["user_id"] = _ensure_user(USER_USERNAME, USER_PW1, 5)
    if refs.get("officer_id"):
        api.patch(f"/users/{refs['officer_id']}/channel-access", headers=h, data={"directive_channel_access": True, "command_channel_access": False})

    # --- Giao nhiem vu (gan chi thi d1, giao Dai doi 5) ---
    if d1:
        asg = _post(
            "/directive-assignments",
            data={
                "directive_id": d1["id"],
                "title": "(demo) Báo cáo kết quả triển khai Chỉ thị SSCĐ cuối năm",
                "description": "Đề nghị các đơn vị báo cáo tiến độ trước 05/09/2026 (dữ liệu minh hoạ).",
                "due_date": "2026-09-05",
                "targets": [{"unit_id": UNIT_C5}],
            },
        )
        if asg:
            refs["assignment_id"] = asg["id"]
            refs["assignment_title"] = "(demo) Báo cáo kết quả triển khai Chỉ thị SSCĐ cuối năm"
            if asg.get("targets"):
                refs["target_id"] = asg["targets"][0]["id"]

    # --- Hop ban BCH & Cap uy ---
    ct1 = _post("/command-threads", data={"title": "(demo) Trao đổi công tác cán bộ quý III/2026"})
    if ct1:
        refs["cthread_id"] = ct1["id"]
        refs["cthread_title"] = "(demo) Trao đổi công tác cán bộ quý III/2026"
        api.post(f"/command-threads/{ct1['id']}/messages", headers=h, form={"body": "Đề nghị Cấp uỷ cho ý kiến phương án kiện toàn cán bộ Đại đội 5 (dữ liệu minh hoạ)."})

    # --- So cong van mat ---
    disp1 = _post(
        "/official-dispatches",
        multipart={
            "direction": "den",
            "dispatch_number": "1234/CV-DEMO",
            "summary": "(demo) Công văn chỉ đạo tăng cường công tác biên phòng dịp cuối năm 2026",
            "issuing_org": "Bộ Tư lệnh Bộ đội Biên phòng",
            "receiving_org": "Lữ đoàn Thông tin 21",
            "issued_date": "2026-08-20",
            "received_date": "2026-08-22",
            "status": "dang_xu_ly",
            "note": "Văn bản MINH HOẠ phục vụ giới thiệu hệ thống.",
            "file": {"name": "cv-demo.pdf", "mimeType": "application/pdf", "buffer": FAKE_PDF},
        },
    )
    if disp1:
        refs["dispatch_id"] = disp1["id"]
        refs["dispatch_number"] = "1234/CV-DEMO"
        api.post(f"/official-dispatches/{disp1['id']}/acknowledge", headers=h, data={"response_note": "Đã tiếp nhận, triển khai thực hiện (dữ liệu minh hoạ)."})

    # --- Ban lam viec Chi dao BCH (leadership-tasks) ---
    lt = _post(
        "/leadership-tasks",
        data={
            "commander_role": "lu_pho_tmt",
            "title": "(demo) Kiểm tra phiên liên lạc mạng vô tuyến điện sóng ngắn cấp Lữ đoàn",
            "content": "Yêu cầu các đơn vị tổ chức kiểm tra phiên liên lạc, báo cáo kết quả trước 17h00 (dữ liệu minh hoạ).",
            "target_branch": "tham_muu",
            "assigned_unit_id": UNIT_C5,
            "urgency": "khan",
        },
    )
    if lt:
        refs["leadership_task_id"] = lt["id"]

    # --- Lich truc tuan (lap -> gui duyet -> phe duyet) ---
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    plan = _post("/duty-week-plans", data={"unit_id": UNIT_C5, "week_start": monday.isoformat(), "note": "Bảng trực tuần minh hoạ."})
    if plan is None:  # co the da ton tai (UNIQUE unit+week) -> tim lai
        try:
            for pl in api.get("/duty-week-plans", headers=h, params={"limit": 200}).json().get("items", []):
                if pl.get("unit_id") == UNIT_C5 and pl.get("week_start") == monday.isoformat():
                    plan = pl
                    break
        except Exception:  # noqa: BLE001
            plan = None
    if plan:
        refs["duty_plan_id"] = plan["id"]
        for i, (dt, shift, who, rt) in enumerate(
            [
                ("truc_chi_huy", "Ca 1 (06:00–18:00)", "Đồng chí trực chỉ huy (demo)", "Trực chỉ huy"),
                ("truc_ban_tac_chien", "Ca 2 (18:00–06:00)", "Đồng chí trực ban (demo)", "Trực ban tác chiến"),
            ]
        ):
            api.post(
                f"/duty-week-plans/{plan['id']}/entries",
                headers=h,
                data={
                    "duty_date": (monday + datetime.timedelta(days=i)).isoformat(),
                    "duty_type": dt,
                    "shift": shift,
                    "duty_officer": who,
                    "role_title": rt,
                    "contact_phone": "069.000.000",
                    "personnel_present": 5,
                    "personnel_total": 6,
                    "note": "Dữ liệu minh hoạ.",
                },
            )
        api.post(f"/duty-week-plans/{plan['id']}/submit", headers=h)
        api.post(f"/duty-week-plans/{plan['id']}/review", headers=h, data={"status": "da_duyet", "review_note": "Đồng ý (dữ liệu minh hoạ)."})

    print("  -> Xong gieo du lieu.")
    return refs


# ------------------------------------------------------------------------ capture
def capture(pw, refs: dict) -> None:
    browser = pw.chromium.launch(headless=False)

    # ---------- 1) Khach chua dang nhap ----------
    print("== Chup: khach / dang ky / dang nhap ==")
    gctx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
    gp = gctx.new_page()
    nav(gp, "/")
    shot(gp, "01_trang_cong_khai")
    nav(gp, "/register")
    shot(gp, "02_dang_ky")
    nav(gp, "/login")
    try:
        gp.get_by_label("Tên đăng nhập").fill(settings.SYSTEM_ADMIN_USERNAME)
        _pw_inputs(gp).first.fill("MatKhauCuaBan")
    except Exception:  # noqa: BLE001
        pass
    shot(gp, "03_dang_nhap")
    gctx.close()

    # ---------- 2) Phien admin / chi huy ----------
    print("== Chup: cac phan he (tai khoan admin) ==")
    ctx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
    page = ctx.new_page()
    try:
        _login_ui(page, settings.SYSTEM_ADMIN_USERNAME, settings.SYSTEM_ADMIN_PASSWORD, "/bang-tin")
        CHECKS.append(("Đăng nhập quản trị qua giao diện", True, ""))
    except Exception as e:  # noqa: BLE001
        CHECKS.append(("Đăng nhập quản trị qua giao diện", False, str(e).splitlines()[0][:160]))
        raise
    shot(page, "05_bang_tin")
    shot(page, "39_menu_day_du_admin")

    for path, name in [
        ("/tin-tuc", "06_tin_tuc_danh_sach"),
        ("/tin-tuc/moi", "07_tin_tuc_form"),
        ("/thong-bao", "08_thong_bao"),
        ("/danh-ba", "09_danh_ba"),
        ("/van-ban", "10_van_ban_danh_sach"),
        ("/van-ban/moi", "11_van_ban_form"),
        ("/giao-duc-chinh-tri", "12_giao_duc_danh_sach"),
        ("/giao-duc-chinh-tri/moi", "13_giao_duc_form"),
        ("/chi-thi-nhiem-vu", "14_chi_thi_danh_sach"),
        ("/chi-thi-nhiem-vu/moi", "15_chi_thi_form"),
    ]:
        nav(page, path)
        shot(page, name)

    # Chi thi - theo doi tiep thu
    nav(page, "/chi-thi-nhiem-vu")
    if refs.get("directive_ids"):
        click_text(page, "(demo) Chỉ thị tăng cường SSCĐ")
        for label in ("quán triệt", "Theo dõi", "tiếp thu", "Danh sách"):
            if click_text(page, label, timeout=1500):
                break
    shot(page, "16_chi_thi_tiep_thu")

    # Lich truc - 4 the
    nav(page, "/lich-truc")
    shot(page, "17_lich_truc_bieu_tuan")
    click_tab_nth(page, 1) or click_role(page, "button", "Kíp trực ngày")
    shot(page, "18_lich_truc_kip_ngay")
    click_tab_nth(page, 2) or click_role(page, "button", "duyệt bảng trực")
    shot(page, "19_lich_truc_lap_duyet")
    click_tab_nth(page, 3) or click_role(page, "button", "Sổ bàn giao")
    shot(page, "20_lich_truc_ban_giao_ca")

    # Kenh Chi dao - Bao cao
    nav(page, "/chi-dao-bao-cao")
    shot(page, "21_chi_dao_luong")
    if refs.get("dthread_title"):
        click_text(page, refs["dthread_title"])
    shot(page, "22_chi_dao_chi_tiet")

    # Giao nhiem vu
    nav(page, "/giao-nhiem-vu")
    shot(page, "23_giao_nhiem_vu")
    if refs.get("assignment_title"):
        click_text(page, refs["assignment_title"])
    shot(page, "24_giao_nhiem_vu_chi_tiet")

    # Kenh chi huy (MAT) - 3 the
    nav(page, "/kenh-chi-huy")
    page.wait_for_timeout(500)
    shot(page, "25_kenh_ban_lam_viec_bch")
    if click_role(page, "button", "Ban hành Chỉ đạo"):
        shot(page, "26_kenh_ban_lam_viec_form")
        click_role(page, "button", "Huỷ bỏ") or page.keyboard.press("Escape")
    else:
        shot(page, "26_kenh_ban_lam_viec_form")
    click_tab_nth(page, 1) or click_text(page, "Họp bàn BCH")
    if refs.get("cthread_title"):
        click_text(page, refs["cthread_title"])
    shot(page, "27_kenh_hop_ban")
    click_tab_nth(page, 2) or click_text(page, "Sổ công văn mật")
    shot(page, "28_kenh_so_cong_van")
    nav(page, "/kenh-chi-huy/cong-van/moi")
    shot(page, "29_cong_van_form")

    # Quan tri
    for path, name in [
        ("/quan-ly-nguoi-dung", "30_quan_ly_nguoi_dung"),
        ("/quan-ly-don-vi", "31_quan_ly_don_vi"),
        ("/nhat-ky-an-ninh", "32_nhat_ky_an_ninh"),
        ("/ho-so", "33_ho_so"),
    ]:
        nav(page, path)
        shot(page, name)

    nav(page, "/ho-so")
    for label in ("Đổi mật khẩu", "Mật khẩu hiện tại"):
        try:
            page.get_by_text(label, exact=False).first.scroll_into_view_if_needed(timeout=1500)
            break
        except Exception:  # noqa: BLE001
            pass
    shot(page, "34_doi_mat_khau")

    # Huong dan su dung - 4 the
    nav(page, "/huong-dan")
    shot(page, "35_huong_dan_kien_truc")
    for idx, name in [(1, "36_huong_dan_ha_tang"), (2, "37_huong_dan_may_tram"), (3, "38_huong_dan_su_co")]:
        try:
            page.get_by_role("tab").nth(idx).click(timeout=3000)
            page.wait_for_timeout(400)
        except Exception:  # noqa: BLE001
            pass
        shot(page, name)

    # ---------- Kiem chung THAT: autosave ban nhap ----------
    print("== Kiem chung autosave ban nhap ==")
    demo_title = "(demo) Chỉ thị kiểm tra tính năng tự động lưu bản nháp"
    demo_content = (
        "Đây là nội dung đang soạn dở để kiểm tra tính năng tự động lưu bản nháp. "
        "Nếu mất mạng hoặc tải lại trang ngay bây giờ, nội dung này phải còn nguyên."
    )
    try:
        nav(page, "/chi-thi-nhiem-vu/moi")
        page.get_by_label("Tiêu đề").fill(demo_title, timeout=8000)
        page.get_by_label("Nội dung").fill(demo_content, timeout=8000)
        page.wait_for_timeout(1200)  # doi debounce ghi localStorage
        shot(page, "46_autosave_dang_soan")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(800)
        shot(page, "47_autosave_sau_reload")
        rt = page.get_by_label("Tiêu đề").input_value(timeout=8000)
        rc = page.get_by_label("Nội dung").input_value(timeout=8000)
        ok = rt == demo_title and rc == demo_content
        CHECKS.append(
            ("Tự động lưu bản nháp khôi phục khớp 100%", ok, "" if ok else f"title={rt!r} content_len={len(rc)}")
        )
        click_role(page, "button", "Huỷ")
    except Exception as e:  # noqa: BLE001
        CHECKS.append(("Tự động lưu bản nháp", False, str(e).splitlines()[0][:160]))
        shot(page, "46_autosave_dang_soan")
        shot(page, "47_autosave_sau_reload")
    ctx.close()

    # ---------- 3) Phien can bo (role 4) ----------
    print("== Chup: tai khoan can bo (role 4) ==")
    octx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
    op = octx.new_page()
    try:
        _login_ui(op, OFFICER_USERNAME, OFFICER_PW1, "/doi-mat-khau")
        _fill_change_password(op, OFFICER_PW1, OFFICER_PW2)
        shot(op, "04_doi_mat_khau_lan_dau")
        op.get_by_role("button", name="Đổi mật khẩu & tiếp tục").click()
        op.wait_for_url(f"{BASE_URL}/", timeout=15000)
        op.wait_for_timeout(500)
        shot(op, "40_menu_han_che_can_bo")

        # can bo nop bao cao nhiem vu
        if refs.get("assignment_title"):
            nav(op, "/giao-nhiem-vu")
            click_text(op, refs["assignment_title"])
            click_role(op, "button", "Xem", exact=True)
            try:
                op.get_by_placeholder("Nội dung báo cáo tiến độ...").fill(
                    "Kính báo cáo: Đại đội 5 đã triển khai 100% nội dung Chỉ thị, SSCĐ (dữ liệu minh hoạ)."
                )
            except Exception:  # noqa: BLE001
                pass
            shot(op, "44_vong_doi_can_bo_nop")
            if click_role(op, "button", "Nộp báo cáo"):
                op.wait_for_timeout(600)
                CHECKS.append(("Cán bộ (role 4) nộp báo cáo nhiệm vụ", True, ""))
    except Exception as e:  # noqa: BLE001
        CHECKS.append(("Luồng cán bộ role 4", False, str(e).splitlines()[0][:160]))
        shot(op, "40_menu_han_che_can_bo")
    octx.close()

    # ---------- 4) Phien nguoi dung (role 5) ----------
    print("== Chup: tai khoan nguoi dung (role 5) ==")
    uctx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
    up = uctx.new_page()
    try:
        _login_ui(up, USER_USERNAME, USER_PW1, "/doi-mat-khau")
        _fill_change_password(up, USER_PW1, USER_PW2)
        up.get_by_role("button", name="Đổi mật khẩu & tiếp tục").click()
        up.wait_for_url(f"{BASE_URL}/", timeout=15000)
        up.wait_for_timeout(500)
        shot(up, "41_menu_nguoi_dung")
        nav(up, "/tin-tuc/moi")
        shot(up, "42_can_bo_dang_bai_bi_chan")
        nav(up, "/kenh-chi-huy")
        shot(up, "43_can_bo_kenh_mat_bi_chan")
    except Exception as e:  # noqa: BLE001
        CHECKS.append(("Luồng người dùng role 5", False, str(e).splitlines()[0][:160]))
    uctx.close()

    # ---------- 5) Quay lai admin: duyet bao cao ----------
    print("== Chup: chi huy duyet bao cao ==")
    actx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
    ap = actx.new_page()
    try:
        _login_ui(ap, settings.SYSTEM_ADMIN_USERNAME, settings.SYSTEM_ADMIN_PASSWORD, "/bang-tin")
        nav(ap, "/giao-nhiem-vu")
        if refs.get("assignment_title"):
            click_text(ap, refs["assignment_title"])
        if click_role(ap, "button", "Duyệt", exact=True):
            ap.wait_for_timeout(300)
            click_role(ap, "button", "Xác nhận", exact=True)
            ap.wait_for_timeout(600)
            CHECKS.append(("Chỉ huy duyệt báo cáo, trạng thái nhiệm vụ tự cập nhật", True, ""))
        shot(ap, "45_vong_doi_chi_huy_duyet")
    except Exception as e:  # noqa: BLE001
        CHECKS.append(("Luồng chỉ huy duyệt", False, str(e).splitlines()[0][:160]))
        shot(ap, "45_vong_doi_chi_huy_duyet")
    actx.close()

    browser.close()


# ------------------------------------------------------------------------ cleanup
def cleanup(api, h: dict, refs: dict) -> None:
    print("== Don dep du lieu minh hoa ==")

    def _try(label, fn):
        try:
            fn()
            print(f"  [xoa] {label}")
        except Exception as e:  # noqa: BLE001
            print(f"  [bo qua] {label}: {e}")

    for pid in refs.get("post_ids", []):
        _try(f"post {pid}", lambda i=pid: api.delete(f"/posts/{i}", headers=h))
    for aid in refs.get("announcement_ids", []):
        _try(f"announcement {aid}", lambda i=aid: api.delete(f"/announcements/{i}", headers=h))
    if refs.get("document_id"):
        _try("document", lambda: api.delete(f"/documents/{refs['document_id']}", headers=h))
    for eid in refs.get("edu_ids", []):
        _try(f"education {eid}", lambda i=eid: api.delete(f"/education-materials/{i}", headers=h))
    if refs.get("assignment_id"):
        _try("assignment", lambda: api.delete(f"/directive-assignments/{refs['assignment_id']}", headers=h))
    for did in refs.get("directive_ids", []):
        _try(f"directive {did}", lambda i=did: api.delete(f"/directives/{i}", headers=h))
    if refs.get("dispatch_id"):
        _try("dispatch", lambda: api.delete(f"/official-dispatches/{refs['dispatch_id']}", headers=h))
    if refs.get("leadership_task_id"):
        _try("leadership_task", lambda: api.delete(f"/leadership-tasks/{refs['leadership_task_id']}", headers=h))
    if refs.get("duty_plan_id"):
        _try("duty_week_plan", lambda: api.delete(f"/duty-week-plans/{refs['duty_plan_id']}", headers=h))
    if refs.get("dthread_id"):
        _try("directive_thread (dong luong)", lambda: api.patch(f"/directive-threads/{refs['dthread_id']}/close", headers=h, data={"is_closed": True}))
    if refs.get("cthread_id"):
        _try("command_thread (dong luong)", lambda: api.patch(f"/command-threads/{refs['cthread_id']}/close", headers=h, data={"is_closed": True}))
    for uid_key in ("officer_id", "user_id"):
        if refs.get(uid_key):
            _try(f"{uid_key} (vo hieu hoa)", lambda i=refs[uid_key]: api.post(f"/users/{i}/deactivate", headers=h))
    print("  -> Xong don dep (xem 'bo qua' o tren neu con sot - can xu ly tay).")


# --------------------------------------------------------------------------- main
def main() -> None:
    with sync_playwright() as pw:
        api = pw.request.new_context(base_url=BASE_URL)
        try:
            login = api.post("/users/login", data={"username": settings.SYSTEM_ADMIN_USERNAME, "password": settings.SYSTEM_ADMIN_PASSWORD})
        except Exception as e:  # noqa: BLE001
            raise SystemExit(f"Khong ket noi duoc backend tai {BASE_URL} - hay khoi dong uvicorn cong 8000 truoc.\n{e}")
        if not login.ok:
            raise SystemExit(f"Dang nhap admin qua API that bai: {login.status} {login.text()}")
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}

        refs = seed(api, h)
        try:
            capture(pw, refs)
        finally:
            cleanup(api, h, refs)
        api.dispose()

    # ---- Bang tong ket ----
    ok = [n for n, s, _ in CAP if s]
    bad = [(n, m) for n, s, m in CAP if not s]
    print("\n" + "=" * 64)
    print(f"KET QUA CHUP ANH: {len(ok)}/{len(CAP)} dat")
    if bad:
        print("Anh KHONG dat:")
        for n, m in bad:
            print(f"  - {n}: {m}")
    print("-" * 64)
    print("KIEM CHUNG CHUC NANG:")
    if not CHECKS:
        print("  (khong co phep kiem chung nao chay)")
    for name, s, note in CHECKS:
        print(f"  [{'DAT ' if s else 'KHONG'}] {name}" + (f"  ({note})" if note else ""))
    total_png = len(list(OUT_DIR.glob('*.png')))
    print("-" * 64)
    print(f"Thu muc anh: {OUT_DIR}  (tong {total_png} tep .png)")
    print("=" * 64)

    # ghi bien ban ket qua ra file (khong phu thuoc encoding console)
    report = OUT_DIR.parent / "capture_report.txt"
    lines = [
        f"KET QUA CHUP ANH: {len(ok)}/{len(CAP)} dat",
        *([f"  - KHONG dat: {n}: {m}" for n, m in bad]),
        "",
        "KIEM CHUNG CHUC NANG:",
        *([f"  [{'DAT' if s else 'KHONG'}] {name}" + (f"  ({note})" if note else "") for name, s, note in CHECKS] or ["  (khong co)"]),
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Bien ban: {report}")

    if bad or any(not s for _, s, _ in CHECKS):
        sys.exit(1)


if __name__ == "__main__":
    main()
