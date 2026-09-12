# -*- coding: utf-8 -*-
"""Sinh TAI LIEU HUONG DAN SU DUNG (Word .docx) kem hinh minh hoa co chu thich.

- Tao ~18 hinh minh hoa (.png) mo phong tung man hinh, danh so (1)(2)(3)... tren cac
  nut / o nhap tuong ung voi cac buoc huong dan.
- Bien soan file Word chi tiet: khai niem, dang nhap, tung chuc nang, xu ly su co,
  phu luc phan quyen.

Chay:
    backend/venv/Scripts/python.exe scripts/build_user_manual.py

Ket qua:
    docs/HUONG_DAN_SU_DUNG.docx
    docs/img/*.png
"""

import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / "docs"
IMG = DOCS / "img"
IMG.mkdir(parents=True, exist_ok=True)

FONTS = pathlib.Path("C:/Windows/Fonts")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


F_TITLE = font("segoeuib.ttf", 20)
F_SUB = font("segoeui.ttf", 13)
F_NAV = font("segoeui.ttf", 15)
F_NAV_B = font("segoeuib.ttf", 15)
F_H1 = font("segoeuib.ttf", 26)
F_H2 = font("segoeuib.ttf", 18)
F_LBL = font("segoeui.ttf", 15)
F_LBL_B = font("segoeuib.ttf", 15)
F_VAL = font("segoeui.ttf", 15)
F_BTN = font("segoeuib.ttf", 15)
F_BADGE = font("segoeuib.ttf", 17)
F_SMALL = font("segoeui.ttf", 13)

W, H = 1440, 940
GREEN = (34, 102, 55)
GREEN_D = (22, 74, 40)
RED = (192, 57, 43)
INK = (33, 37, 41)
GRAY = (108, 117, 125)
LINE = (206, 212, 218)
BG = (244, 246, 244)
PANELBG = (255, 255, 255)
BLUE = (13, 110, 253)
YELLOW = (255, 243, 205)
GREENCHIP = (212, 237, 218)

FULL_MENU = [
    "Bảng tin",
    "Tin tức – Hoạt động",
    "Thông báo – Lịch trực",
    "Văn bản – Tài liệu",
    "Giáo dục chính trị",
    "Chỉ thị – Nhiệm vụ",
    "Chỉ đạo – Báo cáo",
    "Giao nhiệm vụ",
    "Kênh chỉ huy (MẬT)",
    "Hồ sơ cá nhân",
    "Quản lý người dùng",
    "Quản lý đơn vị",
]


# --------------------------------------------------------------------------- kit
def new_canvas(bg=BG):
    im = Image.new("RGB", (W, H), bg)
    return im, ImageDraw.Draw(im)


def text_w(d, s, f):
    return d.textbbox((0, 0), s, font=f)[2]


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def star(d, cx, cy, r, fill=(255, 214, 10)):
    import math

    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=fill)


def chrome(d, page_title, user="Quản trị hệ thống · Admin", active=None, menu=None):
    # window bar
    d.rectangle([0, 0, W, 34], fill=(52, 58, 64))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 22, 12, 28 + i * 22, 24], fill=c)
    d.text((92, 9), "Cổng thông tin điện tử Lữ đoàn Thông tin 21 — trình duyệt", font=F_SMALL, fill=(222, 226, 230))
    # header band
    d.rectangle([0, 34, W, 126], fill=GREEN)
    d.ellipse([24, 50, 84, 110], fill=GREEN_D, outline=(255, 255, 255), width=2)
    star(d, 54, 80, 18)
    d.text((100, 52), "CỔNG THÔNG TIN ĐIỆN TỬ", font=F_TITLE, fill=(255, 255, 255))
    d.text((100, 84), "LỮ ĐOÀN THÔNG TIN 21 – BỘ ĐỘI BIÊN PHÒNG", font=F_SUB, fill=(214, 234, 220))
    # user box
    ux = W - 380
    d.text((ux, 58), "Tài khoản: " + user, font=F_SUB, fill=(255, 255, 255))
    rrect(d, [W - 150, 80, W - 24, 110], 6, fill=GREEN_D)
    d.text((W - 132, 86), "Đăng xuất", font=F_SUB, fill=(255, 255, 255))
    # nav
    d.rectangle([0, 126, W, 172], fill=PANELBG)
    d.line([0, 172, W, 172], fill=LINE, width=1)
    mm = menu if menu is not None else FULL_MENU
    x = 26
    for label in mm:
        is_act = label == active
        f = F_NAV_B if is_act else F_NAV
        d.text((x, 142), label, font=f, fill=(RED if is_act else INK))
        w = text_w(d, label, f)
        if is_act:
            d.line([x, 165, x + w, 165], fill=RED, width=3)
        x += w + 26
        if x > W - 120:
            break
    # page title
    d.text((36, 196), page_title, font=F_H1, fill=INK)
    return 250  # y where content starts


def panel(d, box, title=None):
    rrect(d, box, 10, fill=PANELBG, outline=LINE, width=1)
    if title:
        d.text((box[0] + 18, box[1] + 14), title, font=F_H2, fill=INK)
        return box[1] + 52
    return box[1] + 16


def field(d, x, y, w, label, value="", h=44):
    d.text((x, y), label, font=F_LBL, fill=GRAY)
    rrect(d, [x, y + 22, x + w, y + 22 + h], 6, fill=(252, 252, 252), outline=LINE, width=1)
    d.text((x + 12, y + 22 + (h - 18) // 2), value, font=F_VAL, fill=INK)
    return y + 22 + h + 16


def area(d, x, y, w, h, label, value=""):
    d.text((x, y), label, font=F_LBL, fill=GRAY)
    rrect(d, [x, y + 22, x + w, y + 22 + h], 6, fill=(252, 252, 252), outline=LINE, width=1)
    for i, ln in enumerate(value.split("\n")):
        d.text((x + 12, y + 32 + i * 22), ln, font=F_VAL, fill=INK)
    return y + 22 + h + 16


def button(d, x, y, label, primary=True, n=None):
    w = text_w(d, label, F_BTN) + 40
    rrect(d, [x, y, x + w, y + 40], 6, fill=(RED if primary else (233, 236, 239)))
    d.text((x + 20, y + 10), label, font=F_BTN, fill=((255, 255, 255) if primary else INK))
    if n is not None:
        badge(d, x + w + 20, y + 20, n)
    return x + w + 12


def chip(d, x, y, label, color=GREENCHIP, fg=(30, 111, 52)):
    w = text_w(d, label, F_SMALL) + 22
    rrect(d, [x, y, x + w, y + 24], 12, fill=color)
    d.text((x + 11, y + 4), label, font=F_SMALL, fill=fg)
    return x + w + 8


def table(d, x, y, w, headers, rows, colw=None):
    n = len(headers)
    colw = colw or [w // n] * n
    d.rectangle([x, y, x + sum(colw), y + 34], fill=(238, 240, 242))
    cx = x
    for i, hh in enumerate(headers):
        d.text((cx + 10, y + 8), hh, font=F_LBL_B, fill=INK)
        cx += colw[i]
    ry = y + 34
    for row in rows:
        cx = x
        for i, cell in enumerate(row):
            d.text((cx + 10, ry + 9), str(cell), font=F_SMALL, fill=INK)
            cx += colw[i]
        d.line([x, ry + 34, x + sum(colw), ry + 34], fill=LINE, width=1)
        ry += 34
    d.rectangle([x, y, x + sum(colw), ry], outline=LINE, width=1)
    cx = x
    for i in range(n - 1):
        cx += colw[i]
        d.line([cx, y, cx, ry], fill=LINE, width=1)
    return ry + 12


def badge(d, x, y, n):
    d.ellipse([x - 17, y - 17, x + 17, y + 17], fill=RED, outline=(255, 255, 255), width=3)
    s = str(n)
    bw = text_w(d, s, F_BADGE)
    d.text((x - bw // 2, y - 12), s, font=F_BADGE, fill=(255, 255, 255))


def save(im, name):
    p = IMG / f"{name}.png"
    im.save(p, "PNG")
    print("  đã tạo hình:", p.name)


# ------------------------------------------------------------------- screens
def img_login():
    im, d = new_canvas((238, 242, 238))
    d.rectangle([0, 0, W, 34], fill=(52, 58, 64))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 22, 12, 28 + i * 22, 24], fill=c)
    box = [W // 2 - 260, 170, W // 2 + 260, 620]
    rrect(d, box, 14, fill=PANELBG, outline=LINE, width=1)
    d.ellipse([W // 2 - 34, 210, W // 2 + 34, 278], fill=GREEN)
    star(d, W // 2, 244, 20)
    t = "ĐĂNG NHẬP HỆ THỐNG"
    d.text((W // 2 - text_w(d, t, F_H2) // 2, 300), t, font=F_H2, fill=INK)
    y = field(d, box[0] + 50, 350, 400, "Tên đăng nhập", "admin")
    badge(d, box[0] + 50 + 430, 394, 1)
    y = field(d, box[0] + 50, y, 400, "Mật khẩu", "••••••")
    badge(d, box[0] + 50 + 430, y - 44, 2)
    button(d, box[0] + 50, y + 6, "Đăng nhập", n=3)
    d.text((box[0] + 50, y + 64), "Chưa có tài khoản?  Đăng ký  (chờ chỉ huy duyệt)", font=F_SMALL, fill=BLUE)
    save(im, "01_login")


def img_change_pw():
    im, d = new_canvas()
    cy = chrome(d, "Đổi mật khẩu", active=None, menu=[])
    box = [W // 2 - 300, cy, W // 2 + 300, cy + 470]
    top = panel(d, box, None)
    rrect(d, [box[0] + 18, top, box[2] - 18, top + 60], 6, fill=YELLOW)
    d.text((box[0] + 30, top + 8), "Đây là lần đăng nhập đầu tiên hoặc mật khẩu vừa được", font=F_SMALL, fill=(140, 109, 0))
    d.text((box[0] + 30, top + 30), "cấp lại. Vui lòng đặt mật khẩu mới trước khi tiếp tục.", font=F_SMALL, fill=(140, 109, 0))
    y = top + 78
    y = field(d, box[0] + 40, y, 460, "Mật khẩu hiện tại", "••••••")
    badge(d, box[0] + 40 + 490, y - 44, 1)
    y = field(d, box[0] + 40, y, 460, "Mật khẩu mới  (>= 8 ký tự, có cả chữ và số)", "••••••••••")
    badge(d, box[0] + 40 + 490, y - 44, 2)
    y = field(d, box[0] + 40, y, 460, "Xác nhận mật khẩu mới", "••••••••••")
    badge(d, box[0] + 40 + 490, y - 44, 3)
    button(d, box[0] + 40, y + 6, "Đổi mật khẩu & tiếp tục", n=4)
    save(im, "02_doi_mat_khau")


def img_public():
    im, d = new_canvas()
    d.rectangle([0, 0, W, 34], fill=(52, 58, 64))
    d.rectangle([0, 34, W, 150], fill=GREEN)
    star(d, 50, 92, 18)
    d.text((80, 54), "CỔNG THÔNG TIN ĐIỆN TỬ – LỮ ĐOÀN THÔNG TIN 21", font=F_TITLE, fill=(255, 255, 255))
    d.text((80, 92), "TRUNG THÀNH – MƯU TRÍ – KỊP THỜI – CHÍNH XÁC – BÍ MẬT", font=F_SUB, fill=(214, 234, 220))
    rrect(d, [W - 170, 60, W - 40, 96], 6, fill=(255, 255, 255))
    d.text((W - 150, 68), "Đăng nhập", font=F_SUB, fill=GREEN)
    badge(d, W - 40, 78, 1)
    d.text((60, 190), "Tin tức – Hoạt động đơn vị (công khai)", font=F_H2, fill=INK)
    badge(d, 40, 200, 2)
    for i in range(3):
        bx = [60 + i * 440, 240, 60 + i * 440 + 400, 470]
        rrect(d, bx, 10, fill=PANELBG, outline=LINE, width=1)
        d.rectangle([bx[0] + 12, bx[1] + 12, bx[2] - 12, bx[1] + 130], fill=(222, 226, 230))
        d.text((bx[0] + 14, bx[1] + 150), "Tiêu đề bài viết tuyên truyền…", font=F_LBL_B, fill=INK)
        d.text((bx[0] + 14, bx[1] + 178), "Tóm tắt nội dung bài viết hiển thị ở đây.", font=F_SMALL, fill=GRAY)
    d.text((60, 500), "Thông báo công khai · Văn bản công khai", font=F_H2, fill=INK)
    badge(d, 40, 510, 3)
    save(im, "03_trang_cong_khai")


def _list_detail(d, cy, left_title, items, active_i, detail_title, draw_detail):
    lb = [36, cy, 430, H - 40]
    top = panel(d, lb, left_title)
    for i, it in enumerate(items):
        by = top + i * 66
        if i == active_i:
            rrect(d, [lb[0] + 10, by, lb[2] - 10, by + 58], 6, fill=(255, 245, 244), outline=RED, width=1)
        d.text((lb[0] + 22, by + 8), it[0], font=F_LBL_B, fill=INK)
        d.text((lb[0] + 22, by + 30), it[1], font=F_SMALL, fill=GRAY)
    rb = [450, cy, W - 36, H - 40]
    top = panel(d, rb, detail_title)
    draw_detail(d, rb, top)
    return lb, rb


def img_dashboard():
    im, d = new_canvas()
    cy = chrome(d, "Bảng tin nội bộ", active="Bảng tin")
    for i, (t, sub) in enumerate([("Tin tức mới nhất", "5 bài"), ("Giáo dục chính trị", "3 tài liệu"),
                                  ("Chỉ thị – Nhiệm vụ", "2 chỉ thị"), ("Thông báo", "4 thông báo")]):
        bx = [36 + i * 350, cy, 36 + i * 350 + 320, cy + 150]
        rrect(d, bx, 10, fill=PANELBG, outline=LINE, width=1)
        d.text((bx[0] + 16, bx[1] + 16), t, font=F_LBL_B, fill=INK)
        d.text((bx[0] + 16, bx[1] + 46), sub, font=F_H2, fill=GREEN)
    badge(d, 60, cy + 20, 1)
    d.text((36, cy + 180), "Thanh menu ngang chứa toàn bộ chức năng theo quyền của bạn:", font=F_LBL, fill=INK)
    badge(d, W - 60, 149, 2)
    save(im, "04_bang_tin")


def img_posts():
    im, d = new_canvas()
    cy = chrome(d, "Tin tức – Hoạt động đơn vị", active="Tin tức – Hoạt động")

    def det(d, rb, top):
        y = field(d, rb[0] + 24, top, 620, "Tiêu đề", "Lữ đoàn hoàn thành xuất sắc diễn tập vòng tổng hợp")
        badge(d, rb[0] + 24 + 660, y - 66, 2)
        y = field(d, rb[0] + 24, y, 300, "Danh mục", "Huấn luyện")
        y2 = field(d, rb[0] + 360, y - 60, 260, "Bậc phân loại", "Nội bộ")
        badge(d, rb[0] + 360 + 280, y - 66, 3)
        y = area(d, rb[0] + 24, y, 620, 150, "Nội dung", "Nhập nội dung bài viết…\n(có thể nhiều đoạn)")
        badge(d, rb[0] + 24 + 660, y - 120, 4)
        bx = button(d, rb[0] + 24, y + 4, "Lưu bài")
        button(d, bx, y + 4, "Tải ảnh bìa", primary=False, n=5)

    _list_detail(d, cy, "Danh sách bài viết", [
        ("Diễn tập vòng tổng hợp", "Đã duyệt · 12/08"),
        ("Gương người tốt việc tốt", "Chờ duyệt · 11/08"),
        ("Dân vận vùng biên", "Đã duyệt · 09/08"),
    ], 0, "Soạn / sửa bài viết", det)
    badge(d, 60, cy + 20, 1)
    save(im, "05_tin_tuc")


def img_review():
    im, d = new_canvas()
    cy = chrome(d, "Tin tức – Duyệt bài (chỉ huy)", active="Tin tức – Hoạt động")
    b = [36, cy, W - 36, cy + 360]
    top = panel(d, b, "Bài chờ duyệt: “Gương người tốt việc tốt Đại đội 5”")
    d.text((b[0] + 20, top), "Tác giả: Cán bộ Đại đội 5 · Trạng thái: Chờ duyệt", font=F_LBL, fill=GRAY)
    y = area(d, b[0] + 20, top + 34, b[2] - b[0] - 40, 120, "Nội dung bài", "…")
    y = field(d, b[0] + 20, y, 600, "Ghi chú duyệt / lý do trả lại", "")
    badge(d, b[0] + 20 + 640, y - 66, 2)
    bx = button(d, b[0] + 20, y + 6, "Duyệt đăng")
    button(d, bx, y + 6, "Trả lại tác giả", primary=False, n=3)
    badge(d, 60, cy + 20, 1)
    save(im, "06_duyet_bai")


def img_generic_form(name, title, active, ptitle, fields, extra_note=None):
    im, d = new_canvas()
    cy = chrome(d, title, active=active)
    b = [36, cy, W - 36, cy + 120 + len(fields) * 76 + 90]
    top = panel(d, b, ptitle)
    y = top
    for i, (lbl, val) in enumerate(fields):
        y = field(d, b[0] + 24, y, 700, lbl, val)
        badge(d, b[0] + 24 + 740, y - 66, i + 1)
    button(d, b[0] + 24, y + 6, "Lưu", n=len(fields) + 1)
    if extra_note:
        d.text((b[0] + 24, y + 60), extra_note, font=F_SMALL, fill=GRAY)
    save(im, name)


def img_directive_thread():
    im, d = new_canvas()
    cy = chrome(d, "Kênh Chỉ đạo – Báo cáo", active="Chỉ đạo – Báo cáo")
    rrect(d, [36, cy, W - 36, cy + 44], 6, fill=PANELBG, outline=LINE, width=1)
    d.text((50, cy + 12), "Tiêu đề luồng mới…", font=F_VAL, fill=GRAY)
    button(d, W - 200, cy + 2, "Tạo luồng")
    badge(d, 60, cy + 22, 1)

    def det(d, rb, top):
        d.text((rb[0] + 20, top), "Báo cáo SSCĐ tuần 35 — Tiểu đoàn 1", font=F_LBL_B, fill=INK)
        for i, (who, msg, own) in enumerate([
            ("Ban chỉ huy", "Đề nghị Tiểu đoàn 1 báo cáo trước 16h00.", False),
            ("Tiểu đoàn 1", "Đơn vị đã nhận, sẽ báo cáo đúng hạn. [tệp đính kèm]", True),
        ]):
            mx = rb[0] + (260 if own else 20)
            rrect(d, [mx, top + 40 + i * 90, mx + 520, top + 40 + i * 90 + 74], 8,
                  fill=((240, 247, 255) if own else (245, 245, 245)), outline=LINE, width=1)
            d.text((mx + 12, top + 48 + i * 90), who + " · 30/08 15:20", font=F_SMALL, fill=GRAY)
            d.text((mx + 12, top + 70 + i * 90), msg, font=F_SMALL, fill=INK)
        yy = top + 240
        rrect(d, [rb[0] + 20, yy, rb[2] - 30, yy + 60], 6, fill=(252, 252, 252), outline=LINE, width=1)
        d.text((rb[0] + 32, yy + 8), "Nhập nội dung trao đổi / báo cáo…", font=F_SMALL, fill=GRAY)
        badge(d, rb[0] + 20 + 470, yy + 30, 3)
        bx = button(d, rb[0] + 20, yy + 74, "Chọn tệp", primary=False)
        button(d, bx, yy + 74, "Gửi", n=4)

    _list_detail(d, cy + 60, "Luồng trao đổi", [
        ("Báo cáo SSCĐ tuần 35", "Tiểu đoàn 1 · 3 tin"),
        ("Kế hoạch dã ngoại", "Đại đội 5 · 1 tin"),
    ], 0, "Nội dung trao đổi", det)
    badge(d, 60, cy + 80, 2)
    save(im, "10_chi_dao_luong")


def img_assignment():
    im, d = new_canvas()
    cy = chrome(d, "Giao nhiệm vụ & Báo cáo tiến độ", active="Giao nhiệm vụ")
    fb = [36, cy, W - 36, cy + 300]
    top = panel(d, fb, "Giao nhiệm vụ mới  (chỉ huy)")
    y = field(d, fb[0] + 24, top, 700, "Tiêu đề", "Báo cáo kết quả huấn luyện tuần 35")
    badge(d, fb[0] + 24 + 740, y - 66, 1)
    y2 = field(d, fb[0] + 24, y, 320, "Hạn nộp", "31/12/2026")
    d.text((fb[0] + 380, y), "Giao cho đơn vị:", font=F_LBL, fill=GRAY)
    for i, u in enumerate(["[x] Tiểu đoàn 1", "[x] Đại đội 5", "[  ] Tiểu đoàn 2"]):
        d.text((fb[0] + 380, y + 24 + i * 24), u, font=F_SMALL, fill=INK)
    badge(d, fb[0] + 560, y + 30, 2)
    button(d, fb[0] + 24, y + 110, "Giao nhiệm vụ", n=3)
    tb = [36, cy + 320, W - 36, H - 40]
    top = panel(d, tb, "Chi tiết — trạng thái từng đơn vị")
    ry = table(d, tb[0] + 20, top, tb[2] - tb[0] - 40,
               ["Đơn vị", "Trạng thái", "Số lần nộp", ""],
               [["Tiểu đoàn 1", "Chờ duyệt", "1", "[Xem] [Duyệt]"],
                ["Đại đội 5", "Đã duyệt", "2", "[Xem]"]],
               colw=[260, 200, 160, 640])
    d.text((tb[0] + 20, ry + 6), "Đơn vị: bấm [Xem] để nộp báo cáo (nội dung + tệp).  Chỉ huy: bấm [Duyệt] để Đã duyệt / Trả lại.",
           font=F_SMALL, fill=GRAY)
    save(im, "11_giao_nhiem_vu")


def img_command_channel():
    im, d = new_canvas()
    cy = chrome(d, "Kênh chuyên Ban Chỉ huy & Cấp uỷ  (MẬT)", active="Kênh chỉ huy (MẬT)")
    rrect(d, [36, cy, 360, cy + 40], 6, fill=RED)
    d.text((52, cy + 8), "Họp bàn BCH & Cấp uỷ", font=F_BTN, fill=(255, 255, 255))
    rrect(d, [370, cy, 560, cy + 40], 6, fill=(233, 236, 239))
    d.text((386, cy + 8), "Sổ công văn mật", font=F_BTN, fill=INK)
    badge(d, 200, cy + 20, 1)
    badge(d, 465, cy + 20, 2)

    def det(d, rb, top):
        d.text((rb[0] + 20, top), "Họp bàn Cấp uỷ tuần 35", font=F_LBL_B, fill=INK)
        for i, (who, msg) in enumerate([("Chính uỷ", "Đề nghị các đồng chí cho ý kiến về…"),
                                        ("Phó Lữ trưởng", "Nhất trí phương án 1.")]):
            rrect(d, [rb[0] + 20, top + 36 + i * 76, rb[0] + 520, top + 36 + i * 76 + 60], 8,
                  fill=(245, 245, 245), outline=LINE, width=1)
            d.text((rb[0] + 32, top + 42 + i * 76), who, font=F_SMALL, fill=GRAY)
            d.text((rb[0] + 32, top + 62 + i * 76), msg, font=F_SMALL, fill=INK)
        yy = top + 210
        rrect(d, [rb[0] + 20, yy, rb[2] - 30, yy + 54], 6, fill=(252, 252, 252), outline=LINE, width=1)
        d.text((rb[0] + 32, yy + 8), "Nội dung trao đổi…", font=F_SMALL, fill=GRAY)
        button(d, rb[0] + 20, yy + 66, "Gửi")
        badge(d, rb[0] + 300, yy + 26, 4)

    _list_detail(d, cy + 60, "Các luồng trao đổi", [
        ("Họp bàn Cấp uỷ tuần 35", "5 tin"),
        ("Chủ trương công tác Quý IV", "2 tin"),
    ], 0, "Nội dung", det)
    badge(d, 60, cy + 80, 3)
    save(im, "12a_kenh_chi_huy_hop_ban")


def img_dispatch():
    im, d = new_canvas()
    cy = chrome(d, "Sổ công văn mật  (MẬT)", active="Kênh chỉ huy (MẬT)")
    fb = [36, cy, W - 36, cy + 300]
    top = panel(d, fb, "Vào sổ công văn mới  (chỉ huy)")
    field(d, fb[0] + 24, top, 220, "Chiều", "Văn bản đến")
    field(d, fb[0] + 264, top, 300, "Số / ký hiệu", "123/CV-BTL")
    field(d, fb[0] + 584, top, 220, "Trạng thái", "Mới")
    badge(d, fb[0] + 830, top + 22, 1)
    y = field(d, fb[0] + 24, top + 80, 780, "Trích yếu", "V/v triển khai nhiệm vụ sẵn sàng chiến đấu")
    badge(d, fb[0] + 830, y - 66, 2)
    bx = button(d, fb[0] + 24, y + 6, "Vào sổ")
    button(d, bx, y + 6, "Chọn tệp (.pdf/.docx)", primary=False, n=3)
    tb = [36, cy + 320, W - 36, H - 40]
    top = panel(d, tb, "Chi tiết công văn + tiến độ ký nhận tiếp thu")
    ry = table(d, tb[0] + 20, top, tb[2] - tb[0] - 40,
               ["Người nhận", "Thời gian ký nhận", "Phản hồi thực hiện"],
               [["Lữ trưởng", "30/08 08:10", "Đã quán triệt"],
                ["Chính uỷ", "— chưa ký nhận —", ""]],
               colw=[300, 320, 640])
    bx = button(d, tb[0] + 20, ry + 6, "Ký nhận đã tiếp thu")
    button(d, bx, ry + 6, "Tải tệp công văn", primary=False, n=4)
    save(im, "12b_so_cong_van")


def img_users():
    im, d = new_canvas()
    cy = chrome(d, "Quản lý người dùng", active="Quản lý người dùng")
    fb = [36, cy, W - 36, cy + 250]
    top = panel(d, fb, "Tạo tài khoản trực tiếp")
    field(d, fb[0] + 24, top, 300, "Tên đăng nhập", "canbo.td1")
    field(d, fb[0] + 344, top, 300, "Mật khẩu", "••••••••")
    field(d, fb[0] + 664, top, 260, "Vai trò", "Cán bộ / Nhân viên")
    badge(d, fb[0] + 950, top + 22, 1)
    field(d, fb[0] + 24, top + 78, 300, "Họ tên", "Trần Văn A")
    field(d, fb[0] + 344, top + 78, 300, "Đơn vị", "Tiểu đoàn 1")
    d.text((fb[0] + 664, top + 78), "[x] Cấp quyền vào Kênh Chỉ đạo – Báo cáo", font=F_SMALL, fill=INK)
    badge(d, fb[0] + 620, top + 100, 2)
    button(d, fb[0] + 24, top + 150, "Tạo tài khoản", n=3)
    tb = [36, cy + 270, W - 36, H - 40]
    top = panel(d, tb, "Danh sách tài khoản")
    ry = table(d, tb[0] + 20, top, tb[2] - tb[0] - 40,
               ["Tên ĐN", "Họ tên", "Vai trò", "Đơn vị", "Trạng thái", "Xem MẬT", "Kênh Chỉ đạo", "Hành động"],
               [["canbo.td1", "Trần Văn A", "Cán bộ  v", "Tiểu đoàn 1  v", "Hoạt động", "[  ]", "[x]", "[Khoá] [Cấp lại MK]"],
                ["cs.le", "Lê Văn B", "Chiến sĩ  v", "—  v", "Chờ / khoá", "[  ]", "[  ]", "[Kích hoạt]"]],
               colw=[130, 170, 130, 180, 140, 100, 130, 240])
    d.text((tb[0] + 20, ry + 6), "(1) đổi Vai trò   (2) bật quyền xem MẬT   (3) gán Đơn vị   (4) Kích hoạt tài khoản chờ duyệt   (5) Cấp lại mật khẩu",
           font=F_SMALL, fill=GRAY)
    save(im, "14_quan_ly_nguoi_dung")


def img_units():
    im, d = new_canvas()
    cy = chrome(d, "Quản lý đơn vị", active="Quản lý đơn vị")
    fb = [36, cy, W - 36, cy + 220]
    top = panel(d, fb, "Thêm đơn vị")
    field(d, fb[0] + 24, top, 420, "Tên đơn vị", "Tiểu đoàn 1")
    field(d, fb[0] + 464, top, 300, "Loại đơn vị", "Tiểu đoàn")
    badge(d, fb[0] + 790, top + 22, 1)
    button(d, fb[0] + 24, top + 90, "Thêm đơn vị", n=2)
    tb = [36, cy + 240, W - 36, H - 40]
    top = panel(d, tb, "Danh sách đơn vị")
    table(d, tb[0] + 20, top, tb[2] - tb[0] - 40,
          ["Tên đơn vị", "Loại", "Số tài khoản", "Hoạt động", "Hành động"],
          [["Ban chỉ huy Lữ đoàn", "BCH Lữ đoàn", "4", "[x]", "[Xoá]"],
           ["Cấp uỷ Lữ đoàn", "Cấp uỷ / Đảng bộ", "6", "[x]", "[Xoá]"],
           ["Tiểu đoàn 1", "Tiểu đoàn", "12", "[x]", "[Xoá]"],
           ["Đại đội 5", "Đại đội", "8", "[x]", "[Xoá]"],
           ["Trạm bảo đảm", "Trạm", "3", "[x]", "[Xoá]"]],
          colw=[360, 300, 200, 160, 300])
    d.text((tb[0] + 20, top + 250), "Không xoá được đơn vị khi vẫn còn tài khoản trực thuộc.", font=F_SMALL, fill=GRAY)
    save(im, "15_quan_ly_don_vi")


def img_profile():
    im, d = new_canvas()
    cy = chrome(d, "Hồ sơ cá nhân", active="Hồ sơ cá nhân")
    b = [36, cy, W - 36, cy + 420]
    top = panel(d, b, None)
    d.text((b[0] + 24, top), "Tên đăng nhập: admin      Vai trò: Quản trị hệ thống", font=F_LBL, fill=INK)
    y = field(d, b[0] + 24, top + 40, 480, "Họ tên", "Quản trị hệ thống")
    button(d, b[0] + 24, y + 4, "Lưu thay đổi", n=1)
    y = field(d, b[0] + 620, top + 40, 480, "Mật khẩu hiện tại", "••••••")
    y = field(d, b[0] + 620, y, 480, "Mật khẩu mới", "••••••••")
    button(d, b[0] + 620, y + 4, "Đổi mật khẩu", n=2)
    save(im, "16_ho_so")


def img_menu_officer():
    im, d = new_canvas()
    chrome(d, "Bảng tin  (tài khoản Cán bộ)", user="Trần Văn A · Cán bộ",
           active="Bảng tin",
           menu=["Bảng tin", "Tin tức – Hoạt động", "Thông báo – Lịch trực", "Văn bản – Tài liệu",
                 "Giáo dục chính trị", "Chỉ thị – Nhiệm vụ", "Chỉ đạo – Báo cáo", "Giao nhiệm vụ", "Hồ sơ cá nhân"])
    d.text((36, 260), "Tài khoản Cán bộ được cấp quyền Kênh Chỉ đạo: thấy thêm “Chỉ đạo – Báo cáo”, “Giao nhiệm vụ”.", font=F_LBL, fill=INK)
    d.text((36, 292), "KHÔNG thấy: Kênh chỉ huy (MẬT), Quản lý người dùng, Quản lý đơn vị.", font=F_LBL, fill=RED)
    badge(d, W - 60, 149, 1)
    save(im, "17_menu_can_bo")


def img_menu_soldier():
    im, d = new_canvas()
    chrome(d, "Bảng tin  (tài khoản Chiến sĩ)", user="Lê Văn B · Chiến sĩ", active="Bảng tin",
           menu=["Bảng tin", "Tin tức – Hoạt động", "Thông báo – Lịch trực", "Văn bản – Tài liệu",
                 "Giáo dục chính trị", "Chỉ thị – Nhiệm vụ", "Hồ sơ cá nhân"])
    d.text((36, 260), "Tài khoản Chiến sĩ: chỉ XEM tin tức, giáo dục chính trị, thông báo, chỉ thị.", font=F_LBL, fill=INK)
    d.text((36, 292), "Không có nút đăng / sửa. Không thấy các kênh chỉ đạo và quản trị.", font=F_LBL, fill=RED)
    badge(d, W - 60, 149, 1)
    save(im, "18_menu_chien_si")


def generate_images():
    print("Đang tạo hình minh hoạ…")
    img_login()
    img_change_pw()
    img_public()
    img_dashboard()
    img_posts()
    img_review()
    img_generic_form("07_giao_duc", "Giáo dục chính trị", "Giáo dục chính trị", "Soạn tài liệu giáo dục chính trị",
                     [("Tiêu đề", "Học tập, quán triệt Nghị quyết…"), ("Danh mục", "Học tập chính trị – quân sự"),
                      ("Kỳ áp dụng (tuần/tháng)", "Tuần 35/2026"), ("Nội dung", "…")])
    img_generic_form("08_thong_bao", "Thông báo – Lịch trực kíp", "Thông báo – Lịch trực", "Đăng thông báo nội bộ",
                     [("Tiêu đề", "Lịch trực SSCĐ dịp lễ 02/9"), ("Mức ưu tiên", "Cao"),
                      ("Nội dung", "…")], extra_note="Tick “Ghim lên đầu” và “Công khai” nếu cần. Lịch trực kíp nhập ở thẻ riêng.")
    img_generic_form("09_van_ban", "Văn bản – Tài liệu – Biểu mẫu", "Văn bản – Tài liệu", "Tải lên văn bản / tài liệu",
                     [("Tiêu đề", "Hướng dẫn công tác văn thư"), ("Chuyên mục", "Hướng dẫn"),
                      ("Bậc phân loại", "Nội bộ"), ("Tệp đính kèm", "huong-dan.pdf  [Chọn tệp]")])
    img_generic_form("09b_chi_thi", "Chỉ thị – Nhiệm vụ", "Chỉ thị – Nhiệm vụ", "Ban hành chỉ thị (chỉ chỉ huy)",
                     [("Tiêu đề", "Chỉ thị về tăng cường SSCĐ"), ("Trạng thái", "Đã ban hành"),
                      ("Bậc phân loại", "Nội bộ"), ("Nội dung", "…")],
                     extra_note="Người xem bấm “Tôi đã tiếp thu” để chỉ huy theo dõi mức độ quán triệt.")
    img_directive_thread()
    img_assignment()
    img_command_channel()
    img_dispatch()
    img_users()
    img_units()
    img_profile()
    img_menu_officer()
    img_menu_soldier()


if __name__ == "__main__":
    import sys

    # Tu v7.0.0: HDSD dung ANH CHUP THAT tu he thong (docs/screenshots_khai_thac/,
    # sinh boi scripts/e2e_full_walkthrough.py) thay cho mockup ve tay.
    # Chay lai mockup cu:  python scripts/build_user_manual.py --mockups
    if "--mockups" in sys.argv:
        generate_images()

    shots = ROOT / "docs" / "screenshots_khai_thac"
    n_shots = len(list(shots.glob("*.png"))) if shots.is_dir() else 0
    if n_shots < 20:
        print(
            f"CANH BAO: chi thay {n_shots} anh o {shots}.\n"
            "  -> Chay truoc:  venv/Scripts/python.exe scripts/e2e_full_walkthrough.py\n"
            "     (can backend chay o http://127.0.0.1:8000)."
        )

    from _manual_docx import build_docx  # noqa: E402

    build_docx()
