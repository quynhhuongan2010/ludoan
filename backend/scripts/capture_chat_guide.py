# -*- coding: utf-8 -*-
"""Chup anh minh hoa THAT cho KENH TIN NHAN TAC CHIEN NOI BO (INTRA-CHAT) - day
du toan bo tinh nang toi phien ban hop dong v8.1.0, phuc vu file huong dan
`docs/HUONG_DAN_CHAT_NOI_BO.docx` (build_chat_guide.py).

Cach dung:
    1) Build lai SPA (neu vua sua Frontend):  cd fe-ludoan && npm run build
    2) Khoi dong Backend (phuc vu luon SPA tinh) o cong 8000:
         venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    3) Chay o cua so khac:
         set PYTHONIOENCODING=utf-8
         venv/Scripts/python.exe scripts/capture_chat_guide.py

Lam gi:
    - Tao 4 tai khoan minh hoa (`demo_*`, mat khau `Demo@2026`).
    - Gieo du lieu chat THAT qua API: 1 luong 1-1, 1 nhom DA DUYET (day du: tra
      loi/trich dan, sua tin, thu hoi, tha cam xuc, ghim, chuyen tiep, tin he
      thong, bien nhan da xem, phong QTV nhom), 1 nhom CHO DUYET, 1 nhom da
      TAT THONG BAO + LUU TRU.
    - Dieu khien Chromium that di qua tung man hinh /tin-nhan, chup ~28 anh.
    - Don dep: xoa nhom + luong + tep da gieo; VO HIEU HOA 4 tai khoan demo.

Ket qua: docs/screenshots_khai_thac/chat_*.png
"""

from __future__ import annotations

import io
import pathlib
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.unit import Unit  # noqa: E402
from app.models.user import User  # noqa: E402
from playwright.sync_api import Page, sync_playwright  # noqa: E402

BASE_URL = "http://127.0.0.1:8000"
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "docs" / "screenshots_khai_thac"
OUT_DIR.mkdir(parents=True, exist_ok=True)
VIEWPORT = {"width": 1600, "height": 1000}

PWD = "Demo@2026"
GROUP_NAME = "(demo) Kíp trực SSCĐ – Sở chỉ huy Lữ đoàn"
MUTED_NAME = "(demo) Nhóm hiệp đồng kỹ thuật"
PENDING_NAME = "(demo) Nhóm đề xuất trao đổi công tác Đoàn"

# (username, ho_ten [KHONG kem cap bac], cap_bac, chuc_danh, role)
DEMO_USERS = [
    ("demo_luongtruong", "Nguyễn Văn Sơn", "Đại tá", "Lữ đoàn trưởng", 1),
    ("demo_canbo_a", "Trần Quốc Việt", "Thiếu tá", "Trợ lý Tác chiến", 4),
    ("demo_canbo_b", "Lê Minh Hoàng", "Đại uý", "Đài trưởng", 4),
    ("demo_nguoidung", "Phạm Văn Nam", "Trung uý", "Nhân viên", 5),
]


def _png(text_label: str, color=(31, 76, 48)) -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (1000, 620), color)
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 989, 609], outline=(255, 255, 255), width=4)
    d.text((60, 280), text_label, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("KE_HOACH_SSCD_TUAN.txt", "Noi dung ke hoach (DU LIEU MINH HOA).")
        z.writestr("PHU_LUC_QUAN_SO.csv", "don_vi,quan_so\nSo chi huy,12\nTieu doan 1,120\n")
    return buf.getvalue()


def shot(page: Page, name: str, full_page: bool = False) -> None:
    page.wait_for_timeout(350)
    page.screenshot(path=str(OUT_DIR / f"{name}.png"), full_page=full_page)
    print(f"  [anh] {name}.png")


def compress_shots(max_w: int = 1700, quality: int = 84) -> None:
    """Thu nho + doi PNG -> JPG (file huong dan gon nhe, van du net de in)."""
    from PIL import Image

    n = 0
    for f in sorted(OUT_DIR.glob("chat_*.png")):
        im = Image.open(f).convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        im.save(f.with_suffix(".jpg"), "JPEG", quality=quality, optimize=True, progressive=True)
        f.unlink()
        n += 1
    print(f"Da nen {n} anh -> chat_*.jpg")


def scene(fn):
    """Bao 1 canh chup: loi thi canh bao va di tiep (khong lam hong ca lan chay)."""
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        print(f"  [!] Bo qua 1 canh ({fn.__name__ if hasattr(fn, '__name__') else 'scene'}): {e}")


# --------------------------------------------------------------------------- seed
def ensure_demo_users() -> dict[str, int]:
    ids: dict[str, int] = {}
    with SessionLocal() as db:
        unit_id = db.query(Unit.id).order_by(Unit.id).limit(1).scalar()
        for username, full_name, rank, position, role in DEMO_USERS:
            u = db.query(User).filter(User.username == username).first()
            if not u:
                u = User(username=username)
                db.add(u)
            u.full_name = full_name
            u.rank = rank
            u.position = position
            u.unit_id = unit_id
            u.role = role
            u.is_active = True
            u.must_change_password = False
            u.hashed_password = hash_password(PWD)
            db.flush()
            ids[username] = u.id
        db.commit()
    print("Da tao / cap nhat 4 tai khoan demo_*.")
    return ids


def login_api(api, username: str, password: str) -> dict:
    r = api.post("/users/login", data={"username": username, "password": password})
    if not r.ok:
        raise SystemExit(f"Login API that bai ({username}): {r.status} {r.text()}")
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _msg(api, cid, headers, content, reply_to_id=None):
    body = {"content": content}
    if reply_to_id is not None:
        body["reply_to_id"] = reply_to_id
    return api.post(f"/chats/{cid}/messages", headers=headers, data=body).json()


def seed_chat(api, uids: dict[str, int]) -> dict:
    refs: dict = {}
    h_lt = login_api(api, "demo_luongtruong", PWD)
    h_a = login_api(api, "demo_canbo_a", PWD)
    h_b = login_api(api, "demo_canbo_b", PWD)
    h_nd = login_api(api, "demo_nguoidung", PWD)

    # 1) LUONG 1-1: can bo A <-> Lu truong
    d = api.post("/chats/direct", headers=h_a, data={"recipient_id": uids["demo_luongtruong"]}).json()
    refs["direct_id"] = d["id"]
    _msg(api, d["id"], h_a, "Kính báo cáo Thủ trưởng, đơn vị đã hoàn thành công tác chuẩn bị SSCĐ.")
    _msg(api, d["id"], h_lt, "Rõ. Đồng chí duy trì nghiêm kíp trực, có tình huống báo cáo ngay.")
    _msg(api, d["id"], h_a, "Rõ! Đơn vị chấp hành.")

    # 2) NHOM DA DUYET (Lu truong role 1 tao -> auto da_duyet); ban dau ten ngan,
    #    sau do doi ten qua API de sinh 1 tin he thong minh hoa.
    g = api.post(
        "/chats/group",
        headers=h_lt,
        data={"name": "(demo) Kíp trực SSCĐ", "member_ids": [uids["demo_canbo_a"], uids["demo_canbo_b"]]},
    ).json()
    gid = g["id"]
    refs["group_id"] = gid

    m_lt1 = _msg(api, gid, h_lt, "Các đồng chí báo cáo tình hình kíp trực đầu giờ.")
    _msg(api, gid, h_a, "Trạm 1 thông suốt toàn tuyến, quân số trực 100%.")
    _msg(api, gid, h_b, "Báo cáo Thủ trưởng: Trạm 2 SSCĐ đủ quân số, khí tài kỹ thuật tốt.", reply_to_id=m_lt1["id"])

    api.post(
        f"/chats/{gid}/messages/upload", headers=h_b,
        multipart={
            "content": "Gửi sơ đồ tuyến truyền dẫn dự phòng.",
            "file": {"name": "so-do-truyen-dan.png", "mimeType": "image/png", "buffer": _png("SO DO TUYEN TRUYEN DAN (minh hoa)")},
        },
    )
    m_plan = api.post(
        f"/chats/{gid}/messages/upload", headers=h_lt,
        multipart={
            "content": "Kế hoạch SSCĐ tuần (nén kèm phụ lục).",
            "file": {"name": "ke-hoach-sscd-tuan.zip", "mimeType": "application/zip", "buffer": _zip_bytes()},
        },
    ).json()
    refs["plan_msg_id"] = m_plan["id"]

    # Tha cam xuc len tin "ke hoach"
    for hh, emo in [(h_a, "👍"), (h_b, "🫡"), (h_lt, "✅")]:
        api.post(f"/chats/{gid}/messages/{m_plan['id']}/reactions", headers=hh, data={"emoji": emo})

    m_a2 = _msg(api, gid, h_a, "Đơn vị đã nhận, sẽ triển khai theo kế hoạch.")
    # Sua tin (nguoi gui A)
    api.patch(
        f"/chats/{gid}/messages/{m_a2['id']}",
        headers=h_a,
        data={"content": "Đơn vị đã nhận kế hoạch, sẽ triển khai và báo cáo tiến độ hằng ngày."},
    )
    # Gui nham roi thu hoi
    m_a3 = _msg(api, gid, h_a, "gửi nhầm, xin lỗi Thủ trưởng ạ")
    api.delete(f"/chats/{gid}/messages/{m_a3['id']}", headers=h_a)

    _msg(api, gid, h_a, "⚡ [KHẨN] Đề nghị Sở chỉ huy xác nhận đã nhận kế hoạch.")
    m_lt_last = _msg(
        api, gid, h_lt,
        "Rõ. Sở chỉ huy đã nhận đủ kế hoạch. Các đồng chí duy trì trực nghiêm, có tình huống báo cáo ngay.",
    )
    refs["lt_last_msg_id"] = m_lt_last["id"]

    # Ghim tin "ke hoach"
    api.post(f"/chats/{gid}/messages/{m_plan['id']}/pin", headers=h_lt, data={"pinned": True})
    # Phong can bo A lam QTV nhom
    api.patch(f"/chats/{gid}/members/{uids['demo_canbo_a']}/role", headers=h_lt, data={"is_admin": True})
    # Doi ten nhom -> sinh tin he thong
    api.patch(f"/chats/{gid}", headers=h_lt, data={"name": GROUP_NAME})
    # A va B danh dau da doc -> bien nhan "Da xem (2)" tren tin cuoi cua LT
    api.post(f"/chats/{gid}/read", headers=h_a, data={})
    api.post(f"/chats/{gid}/read", headers=h_b, data={})
    # Chuyen tiep tin "ke hoach" sang luong 1-1
    api.post(
        f"/chats/{gid}/messages/{m_plan['id']}/forward",
        headers=h_lt,
        data={"target_conversation_id": refs["direct_id"]},
    )

    # 3) NHOM CHO DUYET (Nguoi dung role 5 tao)
    gp = api.post(
        "/chats/group",
        headers=h_nd,
        data={"name": PENDING_NAME, "member_ids": [uids["demo_canbo_a"]]},
    ).json()
    refs["pending_id"] = gp["id"]

    # 4) NHOM da TAT THONG BAO + se LUU TRU (LT tao)
    gm = api.post(
        "/chats/group",
        headers=h_lt,
        data={"name": MUTED_NAME, "member_ids": [uids["demo_canbo_b"]]},
    ).json()
    refs["muted_id"] = gm["id"]
    _msg(api, gm["id"], h_b, "Đề nghị hiệp đồng lịch bảo dưỡng khí tài tuần tới.")
    api.post(f"/chats/{gm['id']}/mute", headers=h_lt, data={"muted": True})

    print("Da gieo xong du lieu chat minh hoa (day du tinh nang v8.1.0).")
    return refs


# ------------------------------------------------------------------------ capture
def capture(pw, refs: dict) -> None:
    browser = pw.chromium.launch(headless=False)

    def new_page(username: str) -> Page:
        ctx = browser.new_context(viewport=VIEWPORT, locale="vi-VN", device_scale_factor=2)
        p = ctx.new_page()
        p.goto(f"{BASE_URL}/login", wait_until="networkidle")
        p.locator('input[autocomplete="username"]').fill(username)
        p.locator('input[type="password"]').fill(PWD)
        p.get_by_role("button", name="Đăng nhập").click()
        p.wait_for_url(f"{BASE_URL}/bang-tin", timeout=15000)
        p.wait_for_timeout(400)
        return p

    def open_conv(p: Page, name: str) -> None:
        p.goto(f"{BASE_URL}/tin-nhan", wait_until="networkidle")
        p.wait_for_timeout(900)
        p.get_by_text(name, exact=False).first.click()
        p.wait_for_timeout(800)

    def ensure_drawer(p: Page) -> None:
        if p.locator(".chat-drawer").count() == 0:
            p.locator(".chat-topbar-tools .topbar-tool-btn").last.click()
            p.wait_for_timeout(300)

    def scroll_msgs(p: Page, to_bottom: bool) -> None:
        pos = "el.scrollHeight" if to_bottom else "0"
        p.locator(".chat-messages-area").evaluate(f"el => el.scrollTo(0, {pos})")
        p.wait_for_timeout(400)

    # ================= Phien Lu truong (role 1) =================
    print("== Chup: phien Lu truong ==")
    lt = new_page("demo_luongtruong")
    scene(lambda: shot(lt, "chat_01_bang_tin", full_page=True))

    open_conv(lt, GROUP_NAME)
    scene(lambda: shot(lt, "chat_10_tong_quan"))  # 3 cot + thanh ghim

    def _s_tep():
        scroll_msgs(lt, to_bottom=False)
        shot(lt, "chat_11_khung_chat_tep")
    scene(_s_tep)

    def _s_emoji():
        scroll_msgs(lt, to_bottom=True)
        lt.get_by_role("button", name="Biểu cảm").click()
        lt.wait_for_timeout(300)
        shot(lt, "chat_12_cong_cu_emoji")
        lt.get_by_role("button", name="Biểu cảm").click()
    scene(_s_emoji)

    def _s_reply():
        lt.locator(".msg-quote").first.scroll_into_view_if_needed()
        lt.wait_for_timeout(300)
        shot(lt, "chat_21_tra_loi_trich_dan")
    scene(_s_reply)

    def _s_edit_recall():
        lt.locator(".msg-recalled-text").first.scroll_into_view_if_needed()
        lt.wait_for_timeout(300)
        shot(lt, "chat_22_sua_thu_hoi")
    scene(_s_edit_recall)

    def _s_react():
        row = lt.locator(".msg-row").filter(has=lt.locator(".reaction-chip")).first
        row.scroll_into_view_if_needed()
        lt.locator(".chat-messages-area").evaluate(
            "el => { const r = el.querySelector('.reaction-chip'); if (r) r.scrollIntoView({block:'center'}); }"
        )
        lt.wait_for_timeout(400)
        row.hover()  # hien thanh cong cu tin nhan (co nut 'Tha cam xuc')
        lt.wait_for_timeout(300)
        shot(lt, "chat_23_cam_xuc")
    scene(_s_react)

    def _s_pin():
        scroll_msgs(lt, to_bottom=False)
        lt.locator(".pinned-bar").first.scroll_into_view_if_needed()
        lt.wait_for_timeout(200)
        shot(lt, "chat_24_ghim_tin")
    scene(_s_pin)

    def _s_toolbar():
        row = lt.locator(".msg-row").last
        row.scroll_into_view_if_needed()
        row.hover()
        lt.wait_for_timeout(300)
        shot(lt, "chat_27_thanh_cong_cu_tin_nhan")
    scene(_s_toolbar)

    def _s_forward():
        row = lt.locator(".msg-row").filter(has=lt.locator(".reaction-chip")).first
        row.scroll_into_view_if_needed()
        row.hover()
        lt.wait_for_timeout(200)
        row.locator('.msg-actions button[title="Chuyển tiếp"]').click()
        lt.wait_for_timeout(400)
        shot(lt, "chat_25_chuyen_tiep")
        lt.locator(".chat-modal-head button").click()
    scene(_s_forward)

    def _s_search():
        lt.locator('.chat-topbar-tools button[title="Tìm trong hội thoại"]').click()
        lt.wait_for_timeout(300)
        lt.locator(".conv-search-row input").fill("kế hoạch")
        lt.locator(".conv-search-row button").click()
        lt.wait_for_timeout(600)
        shot(lt, "chat_26_tim_trong_hoi_thoai")
        lt.locator('.chat-topbar-tools button[title="Tìm trong hội thoại"]').click()
    scene(_s_search)

    def _s_system():
        scroll_msgs(lt, to_bottom=True)
        lt.locator(".chat-messages-area").evaluate(
            "el => { const s = el.querySelector('.msg-system-pill'); if (s) s.scrollIntoView({block:'center'}); }"
        )
        lt.wait_for_timeout(300)
        shot(lt, "chat_30_tin_he_thong")
    scene(_s_system)

    def _s_seen():
        scroll_msgs(lt, to_bottom=True)
        lt.wait_for_timeout(300)
        shot(lt, "chat_31_da_xem")
    scene(_s_seen)

    # ------ Modal lap nhom / khoi cho duyet / tu choi ------
    def _s_lapnhom():
        lt.get_by_role("button", name="+ Lập nhóm kíp trực").click()
        lt.wait_for_timeout(400)
        lt.get_by_placeholder("VD: Kíp trực SSCĐ Tiểu đoàn 1, Kíp kỹ thuật...").fill("Kíp trực kỹ thuật Trung tâm 2")
        shot(lt, "chat_13_lap_nhom")
        lt.get_by_role("button", name="Huỷ").click()
    scene(_s_lapnhom)

    scene(lambda: shot(lt, "chat_14_nhom_cho_duyet"))

    def _s_tuchoi():
        lt.locator(".pending-group-item .btn-reject").first.click()
        lt.wait_for_timeout(400)
        lt.get_by_label("Lý do từ chối").fill(
            "Nội dung trùng với nhóm Công tác Đoàn đã có; đề nghị dùng nhóm hiện hành."
        )
        shot(lt, "chat_15_tu_choi_ly_do")
        lt.get_by_role("button", name="Huỷ").click()
    scene(_s_tuchoi)

    # ------ Drawer quan tri nhom ------
    def _s_drawer_rename():
        if lt.locator(".pending-groups-head").count() > 0:
            lt.locator(".pending-groups-head").first.click()
            lt.wait_for_timeout(200)
        ensure_drawer(lt)
        lt.locator(".drawer-rename-btn").first.click()
        lt.wait_for_timeout(300)
        shot(lt, "chat_28_doi_ten_nhom")
        lt.keyboard.press("Escape")
    scene(_s_drawer_rename)

    def _s_drawer_members():
        ensure_drawer(lt)
        lt.locator(".drawer-section").first.scroll_into_view_if_needed()
        lt.wait_for_timeout(200)
        shot(lt, "chat_29_quan_tri_thanh_vien")
    scene(_s_drawer_members)

    def _s_drawer_delete():
        ensure_drawer(lt)
        lt.locator(".drawer-delete-group-btn").first.scroll_into_view_if_needed()
        lt.wait_for_timeout(200)
        shot(lt, "chat_16_drawer_quan_tri")
        lt.locator(".drawer-delete-group-btn").first.click()
        lt.wait_for_timeout(400)
        shot(lt, "chat_17_xac_nhan_xoa_nhom")
        lt.get_by_role("button", name="Huỷ").click()
    scene(_s_drawer_delete)

    # ------ Modal nhan rieng ------
    def _s_nhanrieng():
        lt.get_by_role("button", name="+ Nhắn riêng").click()
        lt.wait_for_timeout(400)
        shot(lt, "chat_18_nhan_rieng")
        lt.keyboard.press("Escape")
    scene(_s_nhanrieng)

    # ------ Tat thong bao (list) + Luu tru (tab) ------
    def _s_muted_list():
        lt.goto(f"{BASE_URL}/tin-nhan", wait_until="networkidle")
        lt.wait_for_timeout(900)
        lt.locator(".conv-muted-tag").first.scroll_into_view_if_needed()
        lt.wait_for_timeout(200)
        lt.locator(".chat-sidebar").screenshot(path=str(OUT_DIR / "chat_34_tat_thong_bao.png"))
        print("  [anh] chat_34_tat_thong_bao.png")
    scene(_s_muted_list)

    def _s_archive_tab():
        open_conv(lt, MUTED_NAME)
        ensure_drawer(lt)
        lt.get_by_role("button", name="Lưu trữ").first.click()  # nut quick-action trong drawer
        lt.wait_for_timeout(700)
        lt.get_by_role("button", name="Lưu trữ").first.click()  # the loc "Luu tru" cot trai
        lt.wait_for_timeout(700)
        lt.locator(".chat-sidebar").screenshot(path=str(OUT_DIR / "chat_35_luu_tru.png"))
        print("  [anh] chat_35_luu_tru.png")
    scene(_s_archive_tab)

    lt.context.close()

    # ================= Truc tuyen + Dang soan tin (2 phien) =================
    print("== Chup: truc tuyen + dang soan tin ==")

    def _s_presence_typing():
        p_lt = new_page("demo_luongtruong")
        p_lt.goto(f"{BASE_URL}/tin-nhan", wait_until="networkidle")
        p_lt.wait_for_timeout(1200)  # de phien LT online

        p_a = new_page("demo_canbo_a")
        open_conv(p_a, GROUP_NAME)
        p_a.wait_for_timeout(1500)
        shot(p_a, "chat_33_truc_tuyen")  # phien A thay LT/ dong chi truc tuyen

        # LT mo dung nhom roi go phim -> phien A hien "... dang soan tin..."
        p_lt.get_by_text(GROUP_NAME, exact=False).first.click()
        p_lt.wait_for_timeout(800)
        p_lt.locator(".chat-input-textarea").click()
        for ch in "Sở chỉ huy đang soạn chỉ thị":
            p_lt.keyboard.type(ch, delay=45)
        p_a.wait_for_selector(".typing-indicator", timeout=4000)
        shot(p_a, "chat_32_dang_soan_tin")
        p_lt.locator(".chat-input-textarea").fill("")
        p_a.context.close()
        p_lt.context.close()
    scene(_s_presence_typing)

    # ================= Phien Nguoi dung (nhom cho duyet bi khoa) =================
    print("== Chup: phien Nguoi dung (nhom cho duyet) ==")

    def _s_pending_user():
        nd = new_page("demo_nguoidung")
        open_conv(nd, PENDING_NAME)
        shot(nd, "chat_19_nguoi_dung_cho_duyet")
        nd.context.close()
    scene(_s_pending_user)

    # ================= Phien Can bo A (chat 1-1 + tin chuyen tiep) =================
    print("== Chup: phien Can bo (chat 1-1) ==")

    def _s_direct():
        ca = new_page("demo_canbo_a")
        open_conv(ca, "Nguyễn Văn Sơn")
        scroll_msgs(ca, to_bottom=True) if ca.locator(".chat-messages-area").count() else None
        ca.wait_for_timeout(400)
        shot(ca, "chat_20_chat_1_1")
        ca.context.close()
    scene(_s_direct)

    browser.close()


# ------------------------------------------------------------------------ cleanup
def cleanup(api, refs: dict, uids: dict) -> None:
    print("== Don dep ==")
    h_adm = login_api(api, settings.SYSTEM_ADMIN_USERNAME, settings.SYSTEM_ADMIN_PASSWORD)

    for key in ("group_id", "pending_id", "muted_id"):
        gid = refs.get(key)
        if gid:
            r = api.delete(f"/chats/{gid}", headers=h_adm)
            print(f"  [xoa nhom] {gid}: {r.status}")

    # Luong 1-1 khong co endpoint xoa -> xoa truc tiep DB + go tep
    with engine.begin() as conn:
        cid = refs.get("direct_id")
        if cid:
            rows = conn.execute(
                text("SELECT attachment_url FROM chat_messages WHERE conversation_id=:c AND attachment_url IS NOT NULL"),
                {"c": cid},
            ).all()
            for (url,) in rows:
                if url and url.startswith("/static/"):
                    fp = ROOT / "backend" / "storage" / "uploads" / url[len("/static/"):]
                    try:
                        fp.unlink()
                    except FileNotFoundError:
                        pass
            conn.execute(text("DELETE FROM chat_message_reactions WHERE message_id IN (SELECT id FROM chat_messages WHERE conversation_id=:c)"), {"c": cid})
            conn.execute(text("DELETE FROM chat_messages WHERE conversation_id=:c"), {"c": cid})
            conn.execute(text("DELETE FROM chat_participants WHERE conversation_id=:c"), {"c": cid})
            conn.execute(text("DELETE FROM chat_conversations WHERE id=:c"), {"c": cid})
    print("  [xoa] luong 1-1 + tep dinh kem")

    with SessionLocal() as db:
        for username in uids:
            u = db.query(User).filter(User.username == username).first()
            if u:
                u.is_active = False
        db.commit()
    print("  [khoa] 4 tai khoan demo_*")


def main() -> None:
    uids = ensure_demo_users()
    with sync_playwright() as pw:
        api = pw.request.new_context(base_url=BASE_URL)
        refs = seed_chat(api, uids)
        try:
            capture(pw, refs)
        finally:
            cleanup(api, refs, uids)
        api.dispose()
    compress_shots()
    n = len(list(OUT_DIR.glob("chat_*.jpg")))
    print(f"\nHOAN TAT. {n} anh chat_*.jpg tai: {OUT_DIR}")


if __name__ == "__main__":
    main()
