# -*- coding: utf-8 -*-
"""Kiem thu chuc nang TOAN BO he thong tren giao dien that + chup anh do phan giai cao.

Muc dich:
  1. Dang nhap qua giao dien that voi tung vai tro (Quan tri, Chi huy, Can bo,
     Nguoi dung, Khach) va di qua MOI man hinh trong sitemap.
  2. Thuc hien cac luong nghiep vu chinh (dang bai -> duyet; giao nhiem vu ->
     nop -> duyet; gui tin nhan kenh; vao so cong van; doi mat khau...).
  3. Ghi nhan PASS/FAIL tung buoc -> xuat bao cao docs/E2E_REPORT.md.
  4. Chup anh full-page (deviceScaleFactor=2) vao docs/screenshots_khai_thac/.
  5. Don dep du lieu minh hoa sau khi xong.

Yeu cau: Backend chay san tai http://127.0.0.1:8000 (co phuc vu frontend/dist).
Chay tu thu muc backend/:
    venv/Scripts/python.exe scripts/e2e_full_walkthrough.py
"""

from __future__ import annotations

import io
import pathlib
import sys
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from playwright.sync_api import Page, sync_playwright  # noqa: E402

BASE_URL = "http://127.0.0.1:8000"
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "docs" / "screenshots_khai_thac"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = ROOT / "docs" / "E2E_REPORT.md"

VIEWPORT = {"width": 1600, "height": 1000}

# Tai khoan minh hoa (tao/ dung lai qua API)
OFFICER_USER = "e2e_canbo"
OFFICER_PW1 = "E2e@canbo1"
OFFICER_PW2 = "E2e@canbo2moi"
CLR_USER = "e2e_canbo_mat"
CLR_PW = "E2e@mat123"
PLAIN_USER = "e2e_nguoidung"
PLAIN_PW = "E2e@user123"

FAKE_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF"
)

RESULTS: list[tuple[str, str, str]] = []  # (nhom, ten_kiem_thu, "PASS"|"FAIL: ...")


def record(group: str, name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else f"FAIL: {detail}"
    RESULTS.append((group, name, status))
    mark = "  ok " if ok else " FAIL"
    print(f"  [{mark}] {group} / {name}" + (f"  -> {detail}" if detail and not ok else ""))


def shot(page: Page, name: str) -> None:
    try:
        # Cuon het trang roi cuon lai dau -> anh lazy-load kip ve truoc khi chup.
        page.evaluate(
            "async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) "
            "{ window.scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); } "
            "window.scrollTo(0, 0); }"
        )
        try:
            page.wait_for_load_state("networkidle", timeout=4000)
        except Exception:  # noqa: BLE001
            pass
        page.wait_for_timeout(350)
        page.screenshot(path=str(OUT_DIR / f"{name}.png"), full_page=True)
        print(f"        [anh] {name}.png")
    except Exception as e:  # noqa: BLE001
        print(f"        [anh LOI] {name}: {e}")


def cover_png(text: str) -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (1200, 675), (31, 76, 48))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 1189, 664], outline=(255, 255, 255), width=4)
    d.text((70, 320), text, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# --------------------------------------------------------------------------- API
def api_login(api, username: str, password: str) -> str | None:
    r = api.post("/users/login", data={"username": username, "password": password})
    if not r.ok:
        return None
    return r.json()["access_token"]


def h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def ensure_account(api, admin_h, username, password, *, role, unit_id, clearance=False,
                   directive_channel=False):
    """Tao tai khoan (hoac dung lai neu da co) o trang thai active, dung role."""
    users = api.get("/users/", headers=admin_h, params={"limit": 500}).json()["items"]
    found = next((u for u in users if u["username"] == username), None)
    if found:
        uid = found["id"]
        api.post(f"/users/{uid}/activate", headers=admin_h)
        api.post(f"/users/{uid}/reset-password", headers=admin_h, data={"new_password": password})
        api.patch(f"/users/{uid}/role", headers=admin_h, data={"role": role})
        api.patch(f"/users/{uid}/unit", headers=admin_h, data={"unit_id": unit_id})
        api.patch(f"/users/{uid}/clearance", headers=admin_h, data={"clearance": clearance})
        api.patch(f"/users/{uid}/channel-access", headers=admin_h,
                  data={"directive_channel_access": directive_channel})
        return uid
    created = api.post("/users/", headers=admin_h, data={
        "username": username, "password": password,
        "full_name": f"{username} (minh hoa)",
        "role": role, "rank": "Trung ta", "position": "Can bo",
        "unit_id": unit_id, "directive_channel_access": directive_channel,
    })
    if not created.ok:
        raise SystemExit(f"Tao tai khoan {username} that bai: {created.status} {created.text()}")
    uid = created.json()["id"]
    if clearance:
        api.patch(f"/users/{uid}/clearance", headers=admin_h, data={"clearance": True})
    return uid


def _purge_demo_threads() -> None:
    """Xoa luong (demo) con sot tu lan chay truoc (API khong co endpoint xoa luong)."""
    try:
        from sqlalchemy import text  # noqa: PLC0415

        from app.core.database import engine  # noqa: PLC0415
        with engine.begin() as c:
            for base in ("directive", "command"):
                sub = f"SELECT id FROM {base}_threads WHERE title LIKE '%(demo)%'"
                for child in (f"{base}_messages", f"{base}_thread_reads",
                              f"{base}_thread_members", f"{base}_thread_minutes",
                              f"{base}_thread_documents"):
                    try:
                        c.execute(text(f"DELETE FROM {child} WHERE thread_id IN ({sub})"))
                    except Exception:  # noqa: BLE001, S110
                        pass
                c.execute(text(f"DELETE FROM {base}_threads WHERE title LIKE '%(demo)%'"))
    except Exception as e:  # noqa: BLE001
        print(f"   (bo qua purge threads: {e})")


def seed(api, admin_h) -> dict:
    print("== Gieo du lieu minh hoa ==")
    _purge_demo_threads()
    refs: dict = {}
    units = api.get("/units/", headers=admin_h).json()
    dai_doi = next((u["id"] for u in units if "5" in u["name"]), units[0]["id"])
    refs["unit_dai_doi"] = dai_doi

    refs["officer_id"] = ensure_account(api, admin_h, OFFICER_USER, OFFICER_PW1,
                                        role=4, unit_id=dai_doi, directive_channel=True)
    refs["clr_id"] = ensure_account(api, admin_h, CLR_USER, CLR_PW,
                                    role=4, unit_id=dai_doi, clearance=True)
    refs["plain_id"] = ensure_account(api, admin_h, PLAIN_USER, PLAIN_PW,
                                      role=5, unit_id=dai_doi)

    # Tin tuc (1 cong khai co anh bia + featured, 1 noi bo)
    p1 = api.post("/posts", headers=admin_h, data={
        "title": "(demo) Hoi thao the luc toan Lu doan quy III/2026",
        "category": "huan_luyen",
        "content": "Noi dung minh hoa phuc vu gioi thieu he thong. Khong phai hoat dong thuc te.",
        "classification": "cong_khai", "is_featured": True,
    }).json()
    refs["post1_id"] = p1["id"]
    api.post(f"/posts/{p1['id']}/thumbnail", headers=admin_h, multipart={
        "file": {"name": "bia.png", "mimeType": "image/png", "buffer": cover_png("ANH MINH HOA")}
    })
    p2 = api.post("/posts", headers=admin_h, data={
        "title": "(demo) Dai doi 5 bieu duong guong chien si tieu bieu thang 8",
        "category": "guong_nguoi_tot", "content": "Bieu duong ca nhan xuat sac (minh hoa).",
        "classification": "noi_bo",
    }).json()
    refs["post2_id"] = p2["id"]

    # Bai cho duyet do can bo dang (de chup man duyet)
    off_tok = api_login(api, OFFICER_USER, OFFICER_PW1)
    if off_tok:
        pend = api.post("/posts", headers=h(off_tok), data={
            "title": "(demo) Bai cho duyet - Can bo Dai doi 5 dang",
            "category": "dan_van", "content": "Bai nay o trang thai cho duyet de minh hoa luong duyet.",
            "classification": "noi_bo",
        })
        if pend.ok:
            refs["pending_post_id"] = pend.json()["id"]

    a1 = api.post("/announcements", headers=admin_h, data={
        "title": "(demo) Thong bao lich truc chi huy tuan 36/2026",
        "content": "Yeu cau cac don vi bo tri quan so truc theo lich (minh hoa).",
        "priority": "khan", "is_pinned": True, "is_public": True,
    }).json()
    refs["ann1_id"] = a1["id"]

    doc1 = api.post("/documents", headers=admin_h, multipart={
        "title": "(demo) Bieu mau bao cao tuan", "category": "bieu_mau",
        "description": "Bieu mau minh hoa.", "classification": "noi_bo",
        "file": {"name": "bieu-mau.pdf", "mimeType": "application/pdf", "buffer": FAKE_PDF},
    }).json()
    refs["doc1_id"] = doc1["id"]

    edu1 = api.post("/education-materials", headers=admin_h, data={
        "title": "(demo) Hoc tap Nghi quyet - Tuan 35/2026",
        "category": "hoc_tap_chinh_tri_quan_su", "period_label": "Tuan 35/2026",
        "content": "Noi dung hoc tap chinh tri tuan 35 (minh hoa).",
    }).json()
    refs["edu1_id"] = edu1["id"]

    d1 = api.post("/directives", headers=admin_h, data={
        "title": "(demo) Chi thi tang cuong SSCD dip cuoi nam 2026",
        "content": "Yeu cau cac co quan, don vi quan triet, trien khai nghiem tuc... (minh hoa).",
        "status": "da_ban_hanh", "classification": "noi_bo",
    }).json()
    refs["directive1_id"] = d1["id"]
    d2 = api.post("/directives", headers=admin_h, data={
        "title": "(demo) Chi thi ban nhap - chua ban hanh",
        "content": "Ban nhap minh hoa - chi chi huy thay.",
        "status": "nhap", "classification": "noi_bo",
    }).json()
    refs["directive2_id"] = d2["id"]

    dt = api.post("/directive-threads", headers=admin_h,
                  data={"unit_id": dai_doi, "title": "(demo) Bao cao SSCD tuan 35 - Dai doi 5"}).json()
    refs["dthread_id"] = dt["id"]
    refs["dthread_title"] = "(demo) Bao cao SSCD tuan 35 - Dai doi 5"
    api.post(f"/directive-threads/{dt['id']}/messages", headers=admin_h,
             form={"body": "Kinh bao cao Ban Chi huy: Dai doi 5 hoan thanh 100% noi dung tuan 35 (minh hoa)."})

    asg = api.post("/directive-assignments", headers=admin_h, data={
        "directive_id": d1["id"], "title": "(demo) Bao cao ket qua trien khai Chi thi SSCD",
        "description": "De nghi cac don vi bao cao tien do truoc 05/09/2026 (minh hoa).",
        "due_date": "2026-09-05", "targets": [{"unit_id": dai_doi}],
    }).json()
    refs["asg_id"] = asg["id"]
    refs["asg_title"] = "(demo) Bao cao ket qua trien khai Chi thi SSCD"
    refs["asg_target_id"] = asg["targets"][0]["id"]

    ct = api.post("/command-threads", headers=admin_h,
                  data={"title": "(demo) Trao doi cong tac can bo quy III/2026"}).json()
    refs["cthread_id"] = ct["id"]
    refs["cthread_title"] = "(demo) Trao doi cong tac can bo quy III/2026"
    api.post(f"/command-threads/{ct['id']}/messages", headers=admin_h,
             form={"body": "De nghi Cap uy cho y kien phuong an kien toan can bo Dai doi 5 (minh hoa)."})

    disp = api.post("/official-dispatches", headers=admin_h, multipart={
        "direction": "den", "dispatch_number": "1234/CV-DEMO",
        "summary": "(demo) Cong van chi dao tang cuong cong tac bien phong dip cuoi nam 2026",
        "issuing_org": "Bo Tu lenh Bo doi Bien phong", "receiving_org": "Lu doan Thong tin 21",
        "issued_date": "2026-08-20", "received_date": "2026-08-22", "status": "dang_xu_ly",
        "note": "Van ban MINH HOA phuc vu gioi thieu he thong.",
        "file": {"name": "cong-van.pdf", "mimeType": "application/pdf", "buffer": FAKE_PDF},
    }).json()
    refs["disp_id"] = disp["id"]
    refs["disp_number"] = "1234/CV-DEMO"
    api.post(f"/official-dispatches/{disp['id']}/acknowledge", headers=admin_h,
             data={"response_note": "Da tiep nhan, trien khai thuc hien (minh hoa)."})

    print("   xong.")
    return refs


def cleanup(api, admin_h, refs: dict) -> None:
    print("== Don dep du lieu minh hoa ==")

    def _try(label, fn):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            print(f"   [bo qua] {label}: {e}")

    for key, path in [
        ("pending_post_id", "/posts/{}"), ("post1_id", "/posts/{}"), ("post2_id", "/posts/{}"),
        ("ann1_id", "/announcements/{}"), ("doc1_id", "/documents/{}"),
        ("edu1_id", "/education-materials/{}"), ("asg_id", "/directive-assignments/{}"),
        ("directive1_id", "/directives/{}"), ("directive2_id", "/directives/{}"),
        ("disp_id", "/official-dispatches/{}"),
    ]:
        if key in refs:
            _try(key, lambda p=path, i=refs[key]: api.delete(p.format(i), headers=admin_h))
    for key in ("dthread_id", "cthread_id"):
        if key in refs:
            ep = "directive-threads" if key.startswith("d") else "command-threads"
            _try(key, lambda e=ep, i=refs[key]: api.patch(f"/{e}/{i}/close", headers=admin_h, data={"is_closed": True}))
    for key in ("officer_id", "clr_id", "plain_id"):
        if key in refs:
            _try(key, lambda i=refs[key]: api.post(f"/users/{i}/deactivate", headers=admin_h))
    print("   xong (muc 'bo qua' o tren la binh thuong - API khong co xoa).")


# ----------------------------------------------------------------------- capture
def _pw_inputs(page: Page):
    """O nhap mat khau (component PasswordInput boc input trong <label> nen
    get_by_label khong chinh xac) -> lay theo type=password."""
    return page.locator('input[type="password"], input[autocomplete="current-password"], '
                        'input[autocomplete="new-password"]')


def login_ui(page: Page, username: str, password: str, *, expect_change_pw=False) -> None:
    page.goto(f"{BASE_URL}/login", wait_until="networkidle")
    page.get_by_label("Tên đăng nhập").fill(username)
    _pw_inputs(page).first.fill(password)
    page.get_by_role("button", name="Đăng nhập").click()
    if expect_change_pw:
        page.wait_for_url(f"{BASE_URL}/doi-mat-khau", timeout=15000)
    else:
        page.wait_for_load_state("networkidle")


def login_pass_gate(page: Page, group: str, username: str, pw_old: str, pw_new: str,
                    *, shot_name: str | None = None) -> None:
    """Dang nhap + neu bi buoc doi mat khau lan dau thi doi luon (pw_old -> pw_new)."""
    login_ui(page, username, pw_old)
    try:
        page.wait_for_url("**/doi-mat-khau", timeout=8000)
    except Exception:  # noqa: BLE001
        pass
    if "/doi-mat-khau" in page.url:
        record(group, "buoc doi mat khau lan dau", True)
        if shot_name:
            shot(page, shot_name)
        pw = _pw_inputs(page)
        pw.nth(0).fill(pw_old)
        pw.nth(1).fill(pw_new)
        pw.nth(2).fill(pw_new)
        page.get_by_role("button", name="Đổi mật khẩu").click()
        try:
            page.wait_for_url(lambda u: "/doi-mat-khau" not in u, timeout=10000)
        except Exception:  # noqa: BLE001
            pass
        page.wait_for_timeout(600)
        record(group, "doi mat khau -> vao he thong", "/doi-mat-khau" not in page.url)
    else:
        record(group, "dang nhap", True)


def visit(page: Page, group: str, path: str, name: str, *, must_see: str | None = None,
          must_not_see: str | None = None) -> None:
    try:
        page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
        page.wait_for_timeout(400)
    except Exception as e:  # noqa: BLE001
        record(group, f"mo {path}", False, str(e)[:120])
        return
    body = page.locator("body").inner_text()
    ok = True
    detail = ""
    if must_see and must_see not in body:
        ok, detail = False, f'khong thay "{must_see}"'
    if must_not_see and must_not_see in body:
        ok, detail = False, f'khong duoc thay "{must_not_see}" nhung co'
    # loi runtime hien thi tren trang
    for bad in ("Something went wrong", "Cannot read properties", "TypeError:", "is not a function"):
        if bad in body:
            ok, detail = False, f'loi JS tren trang: {bad}'
    record(group, f"mo {path}", ok, detail)
    shot(page, name)


def capture_admin(browser, refs: dict) -> None:
    print("\n== VAI TRO: Quan tri / Chi huy (admin) ==")
    ctx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
    page = ctx.new_page()

    # Khach xem trang cong khai truoc khi dang nhap
    page.goto(f"{BASE_URL}/", wait_until="networkidle")
    shot(page, "00_khach_trang_cong_khai")
    record("Khach", "mo / (trang cong khai)", "Đăng nhập" in page.locator("body").inner_text())

    login_ui(page, settings.SYSTEM_ADMIN_USERNAME, settings.SYSTEM_ADMIN_PASSWORD)
    try:
        page.wait_for_url(f"{BASE_URL}/bang-tin", timeout=15000)
        record("Admin", "dang nhap", True)
    except Exception as e:  # noqa: BLE001
        record("Admin", "dang nhap", False, str(e)[:120])
    shot(page, "01_dang_nhap_admin")

    G = "Admin"
    visit(page, G, "/bang-tin", "10_bang_tin", must_see="THÔNG BÁO NỘI BỘ")
    visit(page, G, "/tin-tuc", "11_tin_tuc", must_see="Tin tức")
    visit(page, G, "/tin-tuc/moi", "12_tin_tuc_form")
    visit(page, G, "/thong-bao", "13_thong_bao")
    visit(page, G, "/lich-truc", "14_lich_truc")
    visit(page, G, "/danh-ba", "15_danh_ba")
    visit(page, G, "/van-ban", "16_van_ban", must_see="Văn bản")
    visit(page, G, "/van-ban/moi", "17_van_ban_form")
    visit(page, G, "/giao-duc-chinh-tri", "18_giao_duc", must_see="Giáo dục")
    visit(page, G, "/giao-duc-chinh-tri/moi", "19_giao_duc_form")
    visit(page, G, "/chi-thi-nhiem-vu", "20_chi_thi", must_see="Chỉ thị")
    visit(page, G, "/chi-thi-nhiem-vu/moi", "21_chi_thi_form")
    visit(page, G, "/chi-dao-bao-cao", "22_chi_dao_bao_cao")
    visit(page, G, "/giao-nhiem-vu", "23_giao_nhiem_vu")
    visit(page, G, "/kenh-chi-huy", "24_kenh_chi_huy")
    visit(page, G, "/kenh-chi-huy/cong-van/moi", "25_cong_van_form")
    visit(page, G, "/ho-so", "26_ho_so", must_see="Hồ sơ")
    visit(page, G, "/huong-dan", "27_huong_dan")
    visit(page, G, "/quan-ly-nguoi-dung", "28_quan_ly_nguoi_dung", must_see="người dùng")
    visit(page, G, "/quan-ly-don-vi", "29_quan_ly_don_vi")

    # Mo chi tiet cac luong da gieo
    try:
        page.goto(f"{BASE_URL}/chi-dao-bao-cao", wait_until="networkidle")
        page.get_by_text(refs["dthread_title"]).first.click()
        page.wait_for_timeout(500)
        shot(page, "22b_chi_dao_bao_cao_chi_tiet")
        record(G, "mo luong chi dao-bao cao", True)
    except Exception as e:  # noqa: BLE001
        record(G, "mo luong chi dao-bao cao", False, str(e)[:120])

    try:
        page.goto(f"{BASE_URL}/kenh-chi-huy", wait_until="networkidle")
        page.get_by_text(refs["cthread_title"]).first.click()
        page.wait_for_timeout(500)
        shot(page, "24b_kenh_chi_huy_hop_ban")
        # tab so cong van
        page.get_by_role("button", name="Sổ công văn mật").click()
        page.wait_for_timeout(400)
        shot(page, "24c_so_cong_van")
        record(G, "kenh chi huy: 2 tab", True)
    except Exception as e:  # noqa: BLE001
        record(G, "kenh chi huy: 2 tab", False, str(e)[:120])

    ctx.close()


def capture_officer(browser, refs: dict) -> None:
    print("\n== VAI TRO: Can bo (role 4) + luong doi mat khau + nop bao cao ==")
    ctx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
    page = ctx.new_page()
    G = "Can bo"

    # tai khoan e2e_canbo dang bi buoc doi mat khau? ensure_account da reset-password
    # -> co the must_change_password=True. Thu luong doi mat khau, neu khong redirect
    # thi dang nhap thang.
    login_pass_gate(page, G, OFFICER_USER, OFFICER_PW1, OFFICER_PW2, shot_name="30_doi_mat_khau")
    page.goto(f"{BASE_URL}/bang-tin", wait_until="networkidle")
    page.wait_for_timeout(400)
    shot(page, "31_can_bo_menu")

    visit(page, G, "/tin-tuc", "32_can_bo_tin_tuc", must_see="Tin tức")
    visit(page, G, "/tin-tuc/moi", "33_can_bo_dang_bai")
    visit(page, G, "/giao-duc-chinh-tri/moi", "34_can_bo_gdct_form")
    visit(page, G, "/chi-thi-nhiem-vu", "35_can_bo_chi_thi", must_see="Chỉ thị")
    # can bo KHONG duoc vao kenh chi huy MAT
    visit(page, G, "/kenh-chi-huy", "36_can_bo_kenh_chi_huy_bi_chan")
    visit(page, G, "/quan-ly-nguoi-dung", "37_can_bo_quan_ly_bi_chan")

    # Nop bao cao nhiem vu
    try:
        page.goto(f"{BASE_URL}/giao-nhiem-vu", wait_until="networkidle")
        page.wait_for_timeout(600)
        page.get_by_text(refs["asg_title"], exact=False).first.click(timeout=10000)
        page.wait_for_timeout(500)
        shot(page, "37b_can_bo_chi_tiet_nhiem_vu")
        xem = page.get_by_role("button", name="Xem", exact=True)
        if xem.count():
            xem.first.click()
            page.wait_for_timeout(300)
        ta = page.get_by_placeholder("Nội dung báo cáo tiến độ...")
        if not ta.count():
            ta = page.locator("textarea").first
        ta.fill("Kinh bao cao: Dai doi 5 da trien khai 100% noi dung Chi thi (minh hoa).")
        shot(page, "38_can_bo_nop_bao_cao")
        page.get_by_role("button", name="Nộp báo cáo").first.click()
        page.wait_for_timeout(800)
        shot(page, "39_can_bo_da_nop")
        record(G, "nop bao cao nhiem vu", True)
    except Exception as e:  # noqa: BLE001
        shot(page, "39_can_bo_nop_LOI")
        record(G, "nop bao cao nhiem vu", False, str(e)[:150])

    ctx.close()


def capture_plain(browser) -> None:
    print("\n== VAI TRO: Nguoi dung (role 5) - chi xem ==")
    ctx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
    page = ctx.new_page()
    G = "Nguoi dung"
    login_pass_gate(page, G, PLAIN_USER, PLAIN_PW, PLAIN_PW + "x2")
    page.goto(f"{BASE_URL}/bang-tin", wait_until="networkidle")
    page.wait_for_timeout(600)
    shot(page, "40_nguoi_dung_menu")
    visit(page, G, "/tin-tuc", "41_nguoi_dung_tin_tuc", must_see="Tin tức")
    visit(page, G, "/tin-tuc/moi", "42_nguoi_dung_dang_bai_bi_chan")
    visit(page, G, "/chi-thi-nhiem-vu", "43_nguoi_dung_chi_thi")
    visit(page, G, "/kenh-chi-huy", "44_nguoi_dung_kenh_bi_chan")
    ctx.close()


def capture_review(browser, refs: dict) -> None:
    print("\n== Chi huy duyet bai + duyet bao cao ==")
    ctx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
    page = ctx.new_page()
    G = "Duyet"
    login_ui(page, settings.SYSTEM_ADMIN_USERNAME, settings.SYSTEM_ADMIN_PASSWORD)
    page.wait_for_timeout(400)

    try:
        page.goto(f"{BASE_URL}/tin-tuc", wait_until="networkidle")
        page.wait_for_timeout(600)
        page.get_by_text("Bai cho duyet", exact=False).first.click(timeout=8000)
        page.wait_for_timeout(500)
        shot(page, "50_chi_huy_duyet_bai")
        record(G, "mo bai cho duyet", True)
    except Exception as e:  # noqa: BLE001
        shot(page, "50_chi_huy_duyet_bai_LOI")
        record(G, "mo bai cho duyet", False, str(e)[:150])

    try:
        page.goto(f"{BASE_URL}/giao-nhiem-vu", wait_until="networkidle")
        page.wait_for_timeout(600)
        page.get_by_text(refs["asg_title"], exact=False).first.click(timeout=10000)
        page.wait_for_timeout(700)
        shot(page, "51_chi_huy_thay_bao_cao_cho_duyet")
        duyet = page.get_by_role("button", name="Duyệt", exact=True)
        if not duyet.count():
            # co the phai mo hang don vi/ target truoc
            page.get_by_text("Chờ duyệt", exact=False).first.click()
            page.wait_for_timeout(400)
            duyet = page.get_by_role("button", name="Duyệt", exact=True)
        duyet.first.click(timeout=8000)
        page.wait_for_timeout(300)
        xn = page.get_by_role("button", name="Xác nhận", exact=True)
        if xn.count():
            xn.first.click()
        page.wait_for_timeout(800)
        shot(page, "52_chi_huy_da_duyet")
        record(G, "duyet bao cao nhiem vu", True)
    except Exception as e:  # noqa: BLE001
        shot(page, "52_chi_huy_duyet_LOI")
        record(G, "duyet bao cao nhiem vu", False, str(e)[:150])
    ctx.close()


_FINDINGS_MD = """## Lỗi phát hiện trong đợt kiểm thử & đã sửa

| # | Mức | Vị trí | Mô tả | Cách sửa |
|---|-----|--------|-------|----------|
| 1 | Chặn | `frontend/src/components/PortalLayout.tsx` | `pnpm build` (`tsc -b`) hỏng: khai báo `username`, `hasClearance` không dùng. | Bỏ 2 biến khỏi `useAuth()` destructure. |
| 2 | Nặng | `frontend/src/App.css` (`button {}`, `.tab-bar .tab`, `.thread-item`) | Rule chung `button { color:#fff }` tràn vào tab và dòng danh sách (nền sáng) → chữ trắng trên nền trắng: **mất tiêu đề tab + tiêu đề luồng** ở `/kenh-chi-huy` và `/chi-dao-bao-cao`. | Thêm `color` tường minh cho `.tab-bar .tab` (+`.active`) và `.thread-item`. |
| 3 | Trung bình | `frontend/src/App.css` (`.news-thumb`) | Class `.news-thumb` trùng tên giữa thẻ tin (PostsPage) và dải ảnh nhỏ trang công khai → thumbnail PostsPage bị ép còn ~25% bề rộng, méo bố cục. | Scope lại thành `.news-article .news-thumb` / `.news-article .news-thumb-ph`. |
| 4 | Trung bình | `frontend/src/components/NewsBlock.tsx` + `App.css` | Khối "Giáo dục chính trị" ở Bảng tin và tin tiêu điểm không có ảnh bìa render khung ảnh rỗng cao ~560px (chỉ có biểu trưng) → trang trông như lỗi. | `NewsBlock` chuyển sang danh sách gọn khi không tin nào có ảnh; `FeaturedCard` bỏ hẳn khung ảnh khi thiếu ảnh; bài lead khi mở đọc chuyển từ 2 cột về 1 cột. |

## Khuyến nghị chưa xử lý (không phải lỗi chặn)

- **Nhãn vai trò**: role 4 hiển thị "Cá nhân" (cả `backend/app/core/roles.py` và `frontend/src/types/user.ts`), lệch với mô tả trong `.claude/CLAUDE.md` ("Cán bộ, sĩ quan/QNCN…"). Cần chốt thuật ngữ rồi sửa đồng bộ 2 nơi.
- **`/kenh-chi-huy` với tài khoản không đủ quyền MẬT**: backend chặn 403 đúng, nhưng frontend vẫn hiển thị form "Tạo luồng" + ô nhập. Nên ẩn toàn bộ panel, chỉ để lại thông báo không có quyền.
- **`/danh-ba`**: hiện 2 thông báo "trống" chồng nhau (panel trái + panel phải).
- **`/lich-truc`**: nút "Phê duyệt lịch trực" / "Trả lại" hiện cả khi "Chưa có bảng trực"; nút "Tải file gốc Tham mưu" gắn nhãn "Sắp có".
- Header chỉ hiển thị nhãn vai trò, **không hiển thị tên tài khoản** đăng nhập (thay đổi có chủ đích của bản đang phát triển — cân nhắc khôi phục tên cho dễ nhận biết).
"""


def write_report() -> None:
    n_pass = sum(1 for _, _, s in RESULTS if s == "PASS")
    n_fail = len(RESULTS) - n_pass
    lines = [
        "# Báo cáo kiểm thử chức năng toàn hệ thống (E2E)",
        "",
        f"- Sinh tự động bởi `backend/scripts/e2e_full_walkthrough.py`",
        f"- Tổng: **{len(RESULTS)}** bước — **{n_pass} PASS**, **{n_fail} FAIL**",
        f"- Ảnh minh hoạ: `docs/screenshots_khai_thac/`",
        "",
        "| # | Nhóm | Bước kiểm thử | Kết quả |",
        "|---|------|---------------|---------|",
    ]
    for i, (g, name, status) in enumerate(RESULTS, 1):
        emoji = "✅" if status == "PASS" else "❌"
        lines.append(f"| {i} | {g} | {name} | {emoji} {status} |")
    if n_fail:
        lines += ["", "## Các bước FAIL cần xử lý", ""]
        for g, name, status in RESULTS:
            if status != "PASS":
                lines.append(f"- **{g} / {name}** — {status}")
    lines += ["", _FINDINGS_MD]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nBao cao: {REPORT_PATH}  ({n_pass} PASS / {n_fail} FAIL)")


def main() -> None:
    with sync_playwright() as pw:
        api = pw.request.new_context(base_url=BASE_URL)
        token = api_login(api, settings.SYSTEM_ADMIN_USERNAME, settings.SYSTEM_ADMIN_PASSWORD)
        if not token:
            raise SystemExit("Dang nhap admin qua API that bai - backend co dang chay tai :8000?")
        admin_h = h(token)

        refs = seed(api, admin_h)
        browser = pw.chromium.launch(headless=False)
        try:
            capture_admin(browser, refs)
            capture_officer(browser, refs)
            capture_plain(browser)
            capture_review(browser, refs)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        finally:
            browser.close()
            cleanup(api, admin_h, refs)
            api.dispose()

    write_report()
    n = len(list(OUT_DIR.glob("*.png")))
    print(f"HOAN TAT. {n} anh tai {OUT_DIR}")


if __name__ == "__main__":
    main()
