# -*- coding: utf-8 -*-
"""Chup anh minh hoa THAT tu he thong dang chay (khong phai dung mockup ve tay),
dong thoi la mot buoc KIEM THU CHUC NANG THAT: dang nhap qua giao dien, gui du
lieu qua form thuc te, xac nhan hien thi dung nhu tai lieu gioi thieu.

Cach dung:
    1) Khoi dong Backend (co phuc vu Frontend tinh) tren cong 8000:
       venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    2) Chay o CUA SO KHAC (backend/.env can co SYSTEM_ADMIN_USERNAME/PASSWORD dung):
       venv/Scripts/python.exe scripts/capture_feature_screenshots.py

Lam gi:
    - Dang nhap admin qua API de gieo mot bo DU LIEU MINH HOA toi thieu (tin tuc,
      thong bao, van ban, GDCT, chi thi, luong chi dao, cong van, cuoc hop...) -
      danh dau ro "(demo)" trong tieu de/noi dung de khong lam hai le voi du lieu
      that.
    - Dung trinh duyet那 那(Chromium, that, khong headless-gia) dang nhap qua
      giao dien dang nhap that, di qua tung man hinh, chup anh full-page.
    - Thuc hien tron 1 vong doi "giao nhiem vu -> nop bao cao -> duyet" va 1 phep
      thu "go du 那 lieu -> tai lai trang -> tu khoi phuc ban nhap" bang thao tac
      that tren giao dien (khong gia lap) de vua co anh vua la bang chung hoat
      dong dung.
    - Don dep: xoa/dong lai toan bo du lieu da gieo sau khi chup xong (tru tai
      khoan minh hoa - API khong co xoa tai khoan, se bi VO HIEU HOA thay vi xoa).

Ket qua: anh PNG tai docs/screenshots_khai_thac/*.png (danh so thu tu).
"""

from __future__ import annotations

import datetime
import io
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from playwright.sync_api import Page, sync_playwright  # noqa: E402

BASE_URL = "http://127.0.0.1:8000"
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "docs" / "screenshots_khai_thac"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OFFICER_USERNAME = "demo_canbo_minhhoa"
OFFICER_PASSWORD_1 = "Demo@2026"
OFFICER_PASSWORD_2 = "Demo@2027moi"

FAKE_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF"
)


def make_cover_image(text: str, color=(31, 76, 48)) -> bytes:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (960, 540), color)
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 951, 531], outline=(255, 255, 255), width=3)
    d.text((60, 250), text, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def shot(page: Page, name: str, full_page: bool = True) -> None:
    path = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    print(f"  [anh] {name}.png")


# --------------------------------------------------------------------------- seed
def seed(api, admin_headers: dict) -> dict:
    print("== Dang gieo du lieu minh hoa qua API ==")
    refs: dict = {}
    h = admin_headers

    p1 = api.post(
        "/posts",
        headers=h,
        data={
            "title": "(demo) Hội thao thể lực toàn Lữ đoàn quý III/2026",
            "category": "huan_luyen",
            "content": (
                "Lữ đoàn tổ chức hội thao thể lực toàn đơn vị nhằm nâng cao sức khoẻ, "
                "bản lĩnh chiến đấu cho cán bộ, chiến sĩ. Nội dung này là DỮ LIỆU MINH HOẠ "
                "phục vụ giới thiệu hệ thống, không phải hoạt động thực tế."
            ),
            "classification": "cong_khai",
            "is_featured": True,
        },
    ).json()
    refs["post1_id"] = p1["id"]
    api.post(
        f"/posts/{p1['id']}/thumbnail",
        headers=h,
        multipart={
            "file": {
                "name": "anh-bia-demo.png",
                "mimeType": "image/png",
                "buffer": make_cover_image("ANH MINH HOA HOAT DONG DON VI"),
            }
        },
    )

    p2 = api.post(
        "/posts",
        headers=h,
        data={
            "title": "(demo) Đại đội 5 biểu dương gương chiến sĩ tiêu biểu tháng 8",
            "category": "guong_nguoi_tot",
            "content": "Biểu dương cá nhân có thành tích xuất sắc trong huấn luyện, SSCĐ (dữ liệu minh hoạ).",
            "classification": "noi_bo",
        },
    ).json()
    refs["post2_id"] = p2["id"]

    a1 = api.post(
        "/announcements",
        headers=h,
        data={
            "title": "(demo) Thông báo lịch trực chỉ huy tuần 36/2026",
            "content": "Yêu cầu các đơn vị bố trí quân số trực theo lịch, báo cáo trước 17h00 (dữ liệu minh hoạ).",
            "priority": "khan",
            "is_pinned": True,
            "is_public": True,
        },
    ).json()
    refs["announcement1_id"] = a1["id"]

    doc1 = api.post(
        "/documents",
        headers=h,
        multipart={
            "title": "(demo) Biểu mẫu báo cáo tuần",
            "category": "bieu_mau",
            "description": "Biểu mẫu minh hoạ phục vụ giới thiệu hệ thống.",
            "classification": "noi_bo",
            "file": {"name": "bieu-mau-bao-cao-tuan-demo.pdf", "mimeType": "application/pdf", "buffer": FAKE_PDF},
        },
    ).json()
    refs["document1_id"] = doc1["id"]

    edu1 = api.post(
        "/education-materials",
        headers=h,
        data={
            "title": "(demo) Học tập Nghị quyết - Tuần 35/2026",
            "category": "hoc_tap_chinh_tri_quan_su",
            "period_label": "Tuần 35/2026",
            "content": "Nội dung học tập chính trị tuần 35 (dữ liệu minh hoạ phục vụ giới thiệu hệ thống).",
        },
    ).json()
    refs["edu1_id"] = edu1["id"]

    d1 = api.post(
        "/directives",
        headers=h,
        data={
            "title": "(demo) Chỉ thị tăng cường SSCĐ dịp cuối năm 2026",
            "content": "Yêu cầu các cơ quan, đơn vị quán triệt, triển khai nghiêm túc nội dung sau... (dữ liệu minh hoạ).",
            "status": "da_ban_hanh",
            "classification": "noi_bo",
        },
    ).json()
    refs["directive1_id"] = d1["id"]

    dthread_title = "(demo) Báo cáo SSCĐ tuần 35/2026 - Đại đội 5"
    t1 = api.post("/directive-threads", headers=h, data={"unit_id": 3, "title": dthread_title}).json()
    refs["dthread1_id"] = t1["id"]
    refs["dthread1_title"] = dthread_title
    api.post(
        f"/directive-threads/{t1['id']}/messages",
        headers=h,
        form={"body": "Kính báo cáo Ban Chỉ huy: Đại đội 5 hoàn thành 100% nội dung huấn luyện tuần 35 (dữ liệu minh hoạ)."},
    )

    # tai khoan minh hoa vai tro officer (bi buoc doi mat khau lan dau - dung that).
    # Idempotent: neu lan chay truoc da tao (roi chi vo hieu hoa duoc, khong xoa
    # duoc qua API) thi tai su dung + kich hoat + dat lai mat khau thay vi tao moi.
    existing = [u for u in api.get("/users/", headers=h).json() if u["username"] == OFFICER_USERNAME]
    if existing:
        officer = existing[0]
        api.post(f"/users/{officer['id']}/activate", headers=h)
        api.post(f"/users/{officer['id']}/reset-password", headers=h, data={"new_password": OFFICER_PASSWORD_1})
        api.patch(f"/users/{officer['id']}/role", headers=h, data={"role": "officer"})
        api.patch(f"/users/{officer['id']}/unit", headers=h, data={"unit_id": 3})
        api.patch(
            f"/users/{officer['id']}/channel-access",
            headers=h,
            data={"directive_channel_access": True, "command_channel_access": False},
        )
    else:
        officer = api.post(
            "/users/",
            headers=h,
            data={
                "username": OFFICER_USERNAME,
                "password": OFFICER_PASSWORD_1,
                "full_name": "Nguyễn Văn Cán Bộ (TK minh hoạ)",
                "role": "officer",
                "unit_id": 3,
                "directive_channel_access": True,
            },
        ).json()
    refs["officer_id"] = officer["id"]

    asg_title = "(demo) Báo cáo kết quả triển khai Chỉ thị SSCĐ cuối năm"
    asg = api.post(
        "/directive-assignments",
        headers=h,
        data={
            "directive_id": d1["id"],
            "title": asg_title,
            "description": "Đề nghị các đơn vị báo cáo tiến độ trước 05/09/2026 (dữ liệu minh hoạ).",
            "due_date": "2026-09-05",
            "targets": [{"unit_id": 3}],
        },
    ).json()
    refs["assignment_id"] = asg["id"]
    refs["assignment_title"] = asg_title
    refs["target_id"] = asg["targets"][0]["id"]

    cthread_title = "(demo) Trao đổi công tác cán bộ quý III/2026"
    ct1 = api.post("/command-threads", headers=h, data={"title": cthread_title}).json()
    refs["cthread1_id"] = ct1["id"]
    refs["cthread1_title"] = cthread_title
    api.post(
        f"/command-threads/{ct1['id']}/messages",
        headers=h,
        form={"body": "Đề nghị Cấp uỷ cho ý kiến phương án kiện toàn cán bộ Đại đội 5 (dữ liệu minh hoạ)."},
    )

    disp1 = api.post(
        "/official-dispatches",
        headers=h,
        multipart={
            "direction": "den",
            "dispatch_number": "1234/CV-DEMO",
            "summary": "(demo) Công văn chỉ đạo tăng cường công tác biên phòng dịp cuối năm 2026",
            "issuing_org": "Bộ Tư lệnh Bộ đội Biên phòng",
            "receiving_org": "Lữ đoàn Thông tin 21",
            "issued_date": "2026-08-20",
            "received_date": "2026-08-22",
            "status": "dang_xu_ly",
            "note": "Văn bản MINH HOẠ phục vụ giới thiệu hệ thống, không phải công văn thật.",
            "file": {"name": "cong-van-demo.pdf", "mimeType": "application/pdf", "buffer": FAKE_PDF},
        },
    ).json()
    refs["dispatch1_id"] = disp1["id"]
    refs["dispatch1_number"] = "1234/CV-DEMO"
    api.post(
        f"/official-dispatches/{disp1['id']}/acknowledge",
        headers=h,
        data={"response_note": "Đã tiếp nhận, triển khai thực hiện (dữ liệu minh hoạ)."},
    )

    start = (datetime.datetime.now() + datetime.timedelta(days=2)).replace(microsecond=0, second=0)
    meeting_title = "(demo) Giao ban Ban Chỉ huy & Cấp uỷ tháng 9/2026"
    mtg = api.post(
        "/command-meetings",
        headers=h,
        data={
            "title": meeting_title,
            "start_time": start.isoformat(),
            "location": "Phòng họp Lữ đoàn bộ",
            "agenda": "1. Đánh giá SSCĐ tháng 8.\n2. Triển khai nhiệm vụ tháng 9.\n3. Ý kiến đơn vị. (dữ liệu minh hoạ)",
            "attendee_user_ids": [1],
        },
    ).json()
    refs["meeting1_id"] = mtg["id"]
    refs["meeting1_title"] = meeting_title
    api.post(
        f"/command-meetings/{mtg['id']}/minutes",
        headers=h,
        data={
            "minutes": "Hội nghị thống nhất: hoàn thành 100% chỉ tiêu huấn luyện tháng 8; tập trung SSCĐ dịp Tết trong tháng 9 (dữ liệu minh hoạ).",
            "mark_finished": False,
        },
    )

    print("Da gieo xong du lieu minh hoa.")
    return refs


# ------------------------------------------------------------------------ cleanup
def cleanup(api, admin_headers: dict, refs: dict) -> None:
    print("== Don dep du lieu minh hoa ==")
    h = admin_headers

    def _try(label, fn):
        try:
            fn()
            print(f"  [xoa] {label}")
        except Exception as e:  # noqa: BLE001
            print(f"  [bo qua] {label}: {e}")

    _try("post1", lambda: api.delete(f"/posts/{refs['post1_id']}", headers=h))
    _try("post2", lambda: api.delete(f"/posts/{refs['post2_id']}", headers=h))
    _try("announcement1", lambda: api.delete(f"/announcements/{refs['announcement1_id']}", headers=h))
    _try("document1", lambda: api.delete(f"/documents/{refs['document1_id']}", headers=h))
    _try("edu1", lambda: api.delete(f"/education-materials/{refs['edu1_id']}", headers=h))
    _try("assignment", lambda: api.delete(f"/directive-assignments/{refs['assignment_id']}", headers=h))
    _try("directive1", lambda: api.delete(f"/directives/{refs['directive1_id']}", headers=h))
    _try("dispatch1", lambda: api.delete(f"/official-dispatches/{refs['dispatch1_id']}", headers=h))
    _try("meeting1", lambda: api.delete(f"/command-meetings/{refs['meeting1_id']}", headers=h))
    # directive_threads / command_threads khong co endpoint xoa -> dong luong lai
    _try(
        "dthread1 (dong luong, khong xoa duoc qua API)",
        lambda: api.patch(f"/directive-threads/{refs['dthread1_id']}/close", headers=h, data={"is_closed": True}),
    )
    _try(
        "cthread1 (dong luong, khong xoa duoc qua API)",
        lambda: api.patch(f"/command-threads/{refs['cthread1_id']}/close", headers=h, data={"is_closed": True}),
    )
    # tai khoan minh hoa: khong co endpoint xoa tai khoan -> vo hieu hoa
    _try(
        "tai khoan officer demo (vo hieu hoa, khong xoa duoc qua API)",
        lambda: api.post(f"/users/{refs['officer_id']}/deactivate", headers=h),
    )
    print("Da don dep xong (xem ghi chu 'bo qua' o tren neu co - can xoa tay).")


# ------------------------------------------------------------------------ capture
def capture(pw, refs: dict) -> None:
    # headless=False: dung ban Chromium day du da co san (headless-shell rieng
    # co the chua duoc tai o may nay); van chay tu dong, khong can thao tac tay.
    browser = pw.chromium.launch(headless=False)

    # ---- 1) Khach chua dang nhap: trang cong khai ----
    print("== Chup: khach / dang nhap ==")
    guest_ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="vi-VN")
    gp = guest_ctx.new_page()
    gp.goto(f"{BASE_URL}/", wait_until="networkidle")
    shot(gp, "01_trang_cong_khai_khach")

    gp.goto(f"{BASE_URL}/login", wait_until="networkidle")
    gp.get_by_label("Tên đăng nhập").fill(settings.SYSTEM_ADMIN_USERNAME)
    gp.get_by_label("Mật khẩu").fill(settings.SYSTEM_ADMIN_PASSWORD)
    shot(gp, "02_man_hinh_dang_nhap")
    gp.get_by_role("button", name="Đăng nhập").click()
    gp.wait_for_url(f"{BASE_URL}/bang-tin", timeout=15000)
    guest_ctx.close()

    # ---- 2) Phien admin (thay ca Chi huy) ----
    print("== Chup: cac phan he (tai khoan admin/chi huy) ==")
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="vi-VN")
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/login", wait_until="networkidle")
    page.get_by_label("Tên đăng nhập").fill(settings.SYSTEM_ADMIN_USERNAME)
    page.get_by_label("Mật khẩu").fill(settings.SYSTEM_ADMIN_PASSWORD)
    page.get_by_role("button", name="Đăng nhập").click()
    page.wait_for_url(f"{BASE_URL}/bang-tin", timeout=15000)
    page.wait_for_timeout(500)
    shot(page, "03_bang_tin_tong_hop")

    simple_routes = [
        ("tin-tuc", "04_tin_tuc_hoat_dong_don_vi"),
        ("thong-bao", "05_thong_bao_lich_truc"),
        ("van-ban", "06_van_ban_tai_lieu"),
        ("giao-duc-chinh-tri", "07_giao_duc_chinh_tri"),
        ("chi-thi-nhiem-vu", "08_chi_thi_nhiem_vu"),
    ]
    for path, name in simple_routes:
        page.goto(f"{BASE_URL}/{path}", wait_until="networkidle")
        page.wait_for_timeout(300)
        shot(page, name)

    # ---- Kenh Chi dao - Bao cao: mo luong vua gieo ----
    page.goto(f"{BASE_URL}/chi-dao-bao-cao", wait_until="networkidle")
    page.get_by_text(refs["dthread1_title"]).first.click()
    page.wait_for_timeout(400)
    shot(page, "09_chi_dao_bao_cao_luong")

    # ---- Giao nhiem vu: trang thai TRUOC khi can bo nop bao cao ----
    page.goto(f"{BASE_URL}/giao-nhiem-vu", wait_until="networkidle")
    page.get_by_text(refs["assignment_title"]).first.click()
    page.wait_for_timeout(400)
    shot(page, "10a_giao_nhiem_vu_truoc_khi_nop")

    # ---- Kenh chuyen BCH: tab hop ban + tab so cong van ----
    page.goto(f"{BASE_URL}/kenh-chi-huy", wait_until="networkidle")
    page.get_by_text(refs["cthread1_title"]).first.click()
    page.wait_for_timeout(400)
    shot(page, "11a_kenh_chuyen_bch_hop_ban")

    page.get_by_role("button", name="Sổ công văn mật").click()
    page.wait_for_timeout(300)
    page.get_by_text(refs["dispatch1_number"]).first.click()
    page.wait_for_timeout(400)
    shot(page, "11b_kenh_chuyen_bch_so_cong_van")

    # ---- Giao ban truc tuyen ----
    page.goto(f"{BASE_URL}/giao-ban", wait_until="networkidle")
    page.get_by_text(refs["meeting1_title"]).first.click()
    page.wait_for_timeout(400)
    shot(page, "12_giao_ban_truc_tuyen")

    # ---- Quan ly nguoi dung / Ho so ----
    page.goto(f"{BASE_URL}/quan-ly-nguoi-dung", wait_until="networkidle")
    page.wait_for_timeout(300)
    shot(page, "13_quan_ly_nguoi_dung")

    page.goto(f"{BASE_URL}/ho-so", wait_until="networkidle")
    page.wait_for_timeout(300)
    shot(page, "14_ho_so_ca_nhan")

    # ---- Huong dan su dung: tab 1, 2, 3 (noi dung moi bo sung) ----
    page.goto(f"{BASE_URL}/huong-dan", wait_until="networkidle")
    page.wait_for_timeout(300)
    shot(page, "15a_huong_dan_kien_truc")
    page.get_by_role("tab", name="2. Hạ tầng mạng nội bộ (LAN)").click()
    page.wait_for_timeout(300)
    shot(page, "15b_huong_dan_ha_tang_1click_saoluu")
    page.get_by_role("tab", name="3. Thiết lập máy trạm & người dùng").click()
    page.wait_for_timeout(300)
    shot(page, "15c_huong_dan_autosave")

    # ---- Kiem chung THAT: go du lieu -> tai lai trang -> tu khoi phuc ban nhap ----
    print("== Kiem chung autosave ban nhap (thao tac that + reload that) ==")
    page.goto(f"{BASE_URL}/chi-thi-nhiem-vu", wait_until="networkidle")
    page.get_by_role("button", name="Ban hành chỉ thị mới").click()
    demo_title = "(demo) Chỉ thị kiểm tra tính năng tự động lưu bản nháp"
    demo_content = (
        "Đây là nội dung đang soạn dở để kiểm tra tính năng tự động lưu bản nháp. "
        "Nếu mất mạng hoặc tải lại trang ngay bây giờ, nội dung này phải còn nguyên "
        "khi mở lại form Ban hành chỉ thị mới."
    )
    page.get_by_label("Tiêu đề").fill(demo_title)
    page.get_by_label("Nội dung").fill(demo_content)
    page.wait_for_timeout(800)  # doi debounce ghi localStorage
    shot(page, "16a_autosave_dang_soan_truoc_khi_tai_lai")

    page.reload(wait_until="networkidle")
    page.wait_for_timeout(300)
    page.get_by_role("button", name="Ban hành chỉ thị mới").click()
    page.wait_for_timeout(300)
    shot(page, "16b_autosave_sau_khi_tai_lai_tu_khoi_phuc")

    restored_title = page.get_by_label("Tiêu đề").input_value()
    restored_content = page.get_by_label("Nội dung").input_value()
    ok = restored_title == demo_title and restored_content == demo_content
    print(f"  => KET QUA KIEM CHUNG AUTOSAVE: {'DAT' if ok else 'KHONG DAT'}")
    if not ok:
        print(f"     Ky vong tieu de={demo_title!r} noi dung={demo_content!r}")
        print(f"     Thuc te   tieu de={restored_title!r} noi dung={restored_content!r}")
    # huy form demo, khong luu that vao CSDL
    page.get_by_role("button", name="Huỷ").click()
    refs["autosave_check_ok"] = ok

    # ---- Vong doi: cong bo trang thai admin thay doi sau khi can bo nop (bo sung sau) ----

    ctx.close()

    # ---- 3) Phien can bo (officer) - menu han che + luong doi mat khau + nop bao cao ----
    print("== Chup: tai khoan can bo (officer) ==")
    octx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="vi-VN")
    op = octx.new_page()
    op.goto(f"{BASE_URL}/login", wait_until="networkidle")
    op.get_by_label("Tên đăng nhập").fill(OFFICER_USERNAME)
    op.get_by_label("Mật khẩu").fill(OFFICER_PASSWORD_1)
    op.get_by_role("button", name="Đăng nhập").click()
    op.wait_for_url(f"{BASE_URL}/doi-mat-khau", timeout=15000)
    op.get_by_label("Mật khẩu hiện tại").fill(OFFICER_PASSWORD_1)
    op.get_by_label("Mật khẩu mới", exact=True).fill(OFFICER_PASSWORD_2)
    op.get_by_label("Xác nhận mật khẩu mới").fill(OFFICER_PASSWORD_2)
    shot(op, "17_bat_buoc_doi_mat_khau_lan_dau")
    op.get_by_role("button", name="Đổi mật khẩu & tiếp tục").click()
    op.wait_for_url(f"{BASE_URL}/", timeout=15000)
    op.wait_for_timeout(400)
    shot(op, "18_menu_han_che_theo_quyen_can_bo")

    op.goto(f"{BASE_URL}/giao-nhiem-vu", wait_until="networkidle")
    op.get_by_text(refs["assignment_title"]).first.click()
    op.wait_for_timeout(300)
    op.get_by_role("button", name="Xem", exact=True).click()
    op.wait_for_timeout(300)
    op.get_by_placeholder("Nội dung báo cáo tiến độ...").fill(
        "Kính báo cáo: Đại đội 5 đã triển khai 100% nội dung Chỉ thị, sẵn sàng chiến đấu (dữ liệu minh hoạ)."
    )
    shot(op, "19_can_bo_nop_bao_cao_tien_do")
    op.get_by_role("button", name="Nộp báo cáo").click()
    op.wait_for_timeout(500)
    shot(op, "20_can_bo_da_nop_cho_duyet")
    octx.close()

    # ---- 4) Quay lai admin: duyet bao cao vua nop ----
    print("== Chup: chi huy duyet bao cao ==")
    ctx2 = browser.new_context(viewport={"width": 1440, "height": 900}, locale="vi-VN")
    p2 = ctx2.new_page()
    p2.goto(f"{BASE_URL}/login", wait_until="networkidle")
    p2.get_by_label("Tên đăng nhập").fill(settings.SYSTEM_ADMIN_USERNAME)
    p2.get_by_label("Mật khẩu").fill(settings.SYSTEM_ADMIN_PASSWORD)
    p2.get_by_role("button", name="Đăng nhập").click()
    p2.wait_for_url(f"{BASE_URL}/bang-tin", timeout=15000)

    p2.goto(f"{BASE_URL}/giao-nhiem-vu", wait_until="networkidle")
    p2.get_by_text(refs["assignment_title"]).first.click()
    p2.wait_for_timeout(400)
    shot(p2, "21a_chi_huy_thay_bao_cao_cho_duyet")
    p2.get_by_role("button", name="Duyệt", exact=True).click()
    p2.wait_for_timeout(200)
    p2.get_by_role("button", name="Xác nhận", exact=True).click()
    p2.wait_for_timeout(500)
    shot(p2, "21b_chi_huy_da_duyet_hoan_thanh")
    ctx2.close()

    browser.close()


def main() -> None:
    with sync_playwright() as pw:
        api = pw.request.new_context(base_url=BASE_URL)
        login = api.post(
            "/users/login",
            data={"username": settings.SYSTEM_ADMIN_USERNAME, "password": settings.SYSTEM_ADMIN_PASSWORD},
        )
        if not login.ok:
            raise SystemExit(f"Dang nhap admin qua API that bai: {login.status} {login.text()}")
        token = login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {token}"}

        refs = seed(api, admin_headers)
        try:
            capture(pw, refs)
        finally:
            cleanup(api, admin_headers, refs)
        api.dispose()

    n = len(list(OUT_DIR.glob("*.png")))
    print(f"\nHOAN TAT. {n} anh da luu tai: {OUT_DIR}")
    if not refs.get("autosave_check_ok", True):
        print("CANH BAO: kiem chung autosave KHONG DAT - xem log o tren.")


if __name__ == "__main__":
    main()
