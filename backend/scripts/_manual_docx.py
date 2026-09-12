# -*- coding: utf-8 -*-
"""Bien soan file Word HUONG_DAN_SU_DUNG.docx (goi tu build_user_manual.py)."""

import datetime
import pathlib

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / "docs"
IMG = DOCS / "img"
SHOTS = DOCS / "screenshots_khai_thac"  # anh chup THAT tu he thong dang chay
OUT = DOCS / "HUONG_DAN_SU_DUNG.docx"

# Anh chup that thay cho mockup ve tay. Sinh boi:
#   backend/scripts/e2e_full_walkthrough.py  (cAn backend chay o :8000)
FIGURE_MAP = {
    "01_login": "01_dang_nhap_admin",
    "02_doi_mat_khau": "30_doi_mat_khau",
    "03_trang_cong_khai": "00_khach_trang_cong_khai",
    "04_bang_tin": "10_bang_tin",
    "05_tin_tuc": "11_tin_tuc",
    "06_duyet_bai": "50_chi_huy_duyet_bai",
    "07_giao_duc": "18_giao_duc",
    "08_thong_bao": "13_thong_bao",
    "08b_lich_truc": "14_lich_truc",
    "08c_danh_ba": "15_danh_ba",
    "09_van_ban": "16_van_ban",
    "09b_chi_thi": "20_chi_thi",
    "10_chi_dao_luong": "22_chi_dao_bao_cao",
    "11_giao_nhiem_vu": "23_giao_nhiem_vu",
    "11b_nop_bao_cao": "38_can_bo_nop_bao_cao",
    "11c_duyet_bao_cao": "52_chi_huy_da_duyet",
    "12a_kenh_chi_huy_hop_ban": "24_kenh_chi_huy",
    "12b_so_cong_van": "24c_so_cong_van",
    "14_quan_ly_nguoi_dung": "28_quan_ly_nguoi_dung",
    "15_quan_ly_don_vi": "29_quan_ly_don_vi",
    "16_ho_so": "26_ho_so",
    "17_menu_can_bo": "31_can_bo_menu",
    "18_menu_chien_si": "40_nguoi_dung_menu",
    "19_kenh_bi_chan": "36_can_bo_kenh_chi_huy_bi_chan",
}

GREEN = RGBColor(0x22, 0x66, 0x37)
DARK = RGBColor(0x21, 0x25, 0x29)
GRAYTXT = RGBColor(0x66, 0x66, 0x66)


# --------------------------------------------------------------------- helpers
def _shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def _page_field(paragraph):
    run = paragraph.add_run()
    for kind, txt in [("begin", None), ("instrText", " PAGE "), ("separate", None), ("t", "1"), ("end", None)]:
        el = OxmlElement(f"w:{kind}")
        if kind == "instrText":
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        elif kind == "t":
            el.text = txt
        else:
            el.set(qn("w:fldCharType"), kind)
        run._r.append(el)


class M:
    def __init__(self):
        d = Document()
        self.d = d
        st = d.styles["Normal"]
        st.font.name = "Times New Roman"
        st.font.size = Pt(12)
        for i, sz in [(1, 17), (2, 14), (3, 12.5)]:
            h = d.styles[f"Heading {i}"]
            h.font.name = "Times New Roman"
            h.font.size = Pt(sz)
            h.font.color.rgb = GREEN
            h.font.bold = True
        sec = d.sections[0]
        sec.page_width = Inches(8.27)
        sec.page_height = Inches(11.69)
        for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(sec, m, Inches(0.8))
        # footer page number
        fp = sec.footer.paragraphs[0]
        fp.text = "Hướng dẫn sử dụng – Cổng thông tin Lữ đoàn Thông tin 21   |   Trang "
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in fp.runs:
            r.font.size = Pt(9)
            r.font.color.rgb = GRAYTXT
        _page_field(fp)

    # -- primitives -------------------------------------------------------
    def h(self, level, text):
        self.d.add_heading(text, level=level)

    def p(self, text, bold=False, italic=False, color=None, size=None):
        par = self.d.add_paragraph()
        r = par.add_run(text)
        r.bold = bold
        r.italic = italic
        if color:
            r.font.color.rgb = color
        if size:
            r.font.size = Pt(size)
        return par

    def steps(self, items):
        for it in items:
            self.d.add_paragraph(str(it), style="List Number")

    def bullets(self, items):
        for it in items:
            self.d.add_paragraph(str(it), style="List Bullet")

    def note(self, text, fill="FFF3CD", label="LƯU Ý"):
        t = self.d.add_table(rows=1, cols=1)
        t.autofit = True
        c = t.cell(0, 0)
        _shade(c, fill)
        c.paragraphs[0].text = ""
        run = c.paragraphs[0].add_run(f"⚠ {label}: ")
        run.bold = True
        c.paragraphs[0].add_run(text)
        for r in c.paragraphs[0].runs:
            r.font.size = Pt(11)
        self.d.add_paragraph()

    def figure(self, name, caption):
        # Uu tien anh chup THAT (screenshots_khai_thac), roi den ten da anh xa,
        # cuoi cung moi den mockup cu trong docs/img.
        real = FIGURE_MAP.get(name, name)
        path = None
        for cand in (SHOTS / f"{real}.png", SHOTS / f"{name}.png", IMG / f"{name}.png"):
            if cand.exists():
                path = cand
                break
        if path is None:
            self.p(f"[Thiếu hình: {name}]", italic=True, color=GRAYTXT)
            return
        # Anh chup that thuong rat cao (full-page) -> gioi han CA be rong lan
        # chieu cao de vua 1 trang A4, khong bi Word cat. Be rong 6.6" = gan het
        # vung in (kho A4 8.27" - le 2x0.8") de anh to, ro chu hon.
        max_w, max_h = Inches(6.6), Inches(8.7)
        w, h = max_w, None
        try:
            from PIL import Image  # noqa: PLC0415

            with Image.open(path) as im:
                pw, ph = im.size
            h = int(max_w * ph / pw)
            if h > max_h:
                h = max_h
                w = int(max_h * pw / ph)
        except Exception:  # noqa: BLE001
            h = None
        if h:
            self.d.add_picture(str(path), width=w, height=h)
        else:
            self.d.add_picture(str(path), width=w)
        self.d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = self.d.add_paragraph(f"Ảnh màn hình: {caption}")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in cap.runs:
            r.italic = True
            r.font.size = Pt(10)
            r.font.color.rgb = GRAYTXT
        self.d.add_paragraph()

    def table(self, headers, rows, widths=None):
        t = self.d.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        for i, htext in enumerate(headers):
            cell = t.rows[0].cells[i]
            cell.text = ""
            run = cell.paragraphs[0].add_run(htext)
            run.bold = True
            run.font.size = Pt(10.5)
            _shade(cell, "E7ECEA")
        for row in rows:
            cells = t.add_row().cells
            for i, val in enumerate(row):
                cells[i].text = ""
                run = cells[i].paragraphs[0].add_run(str(val))
                run.font.size = Pt(10.5)
        if widths:
            for i, w in enumerate(widths):
                for r in t.rows:
                    r.cells[i].width = Inches(w)
        self.d.add_paragraph()

    def toc(self):
        par = self.d.add_paragraph()
        run = par.add_run()
        for kind, txt in [("begin", None), ("instrText", 'TOC \\o "1-3" \\h \\z \\u'),
                          ("separate", None), ("t", "Mở tài liệu bằng Microsoft Word, bấm chuột phải vào mục lục này rồi chọn “Update Field” để hiện số trang."),
                          ("end", None)]:
            el = OxmlElement(f"w:{kind}")
            if kind == "instrText":
                el.set(qn("xml:space"), "preserve")
                el.text = txt
            elif kind == "t":
                el.text = txt
            else:
                el.set(qn("w:fldCharType"), kind)
            run._r.append(el)

    def pagebreak(self):
        self.d.add_page_break()

    def save(self):
        self.d.save(str(OUT))


# --------------------------------------------------------------------- content
def build_docx():
    m = M()
    d = m.d
    today = datetime.date.today().strftime("%d/%m/%Y")

    # ---- COVER ----
    for _ in range(3):
        d.add_paragraph()
    t = d.add_paragraph("HƯỚNG DẪN SỬ DỤNG")
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.runs[0].bold = True
    t.runs[0].font.size = Pt(30)
    t.runs[0].font.color.rgb = GREEN
    s = d.add_paragraph("CỔNG THÔNG TIN ĐIỆN TỬ NỘI BỘ\nLỮ ĐOÀN THÔNG TIN 21 – BỘ ĐỘI BIÊN PHÒNG")
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s.runs[0].font.size = Pt(15)
    s.runs[0].bold = True
    for _ in range(2):
        d.add_paragraph()
    box = d.add_table(rows=1, cols=1)
    box.style = "Table Grid"
    c = box.cell(0, 0)
    _shade(c, "F2F6F2")
    c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line in ["Phiên bản hợp đồng API: v7.0.0",
                 f"Ngày biên soạn: {today}",
                 "Đối tượng: mọi cán bộ, quân nhân chuyên nghiệp được cấp tài khoản",
                 "Bộ phận kỹ thuật: xem Mục 3 để cài đặt và bàn giao",
                 "Hình minh hoạ trong tài liệu là ẢNH CHỤP THẬT từ hệ thống đang chạy",
                 "LƯU HÀNH NỘI BỘ"]:
        pr = c.add_paragraph(line)
        pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pr.runs[0].font.size = Pt(12)
        if line == "LƯU HÀNH NỘI BỘ":
            pr.runs[0].bold = True
            pr.runs[0].font.color.rgb = RGBColor(0xC0, 0x39, 0x2B)
    c.paragraphs[0].text = ""
    m.pagebreak()

    # ---- TOC ----
    m.h(1, "MỤC LỤC")
    m.toc()
    m.pagebreak()

    # ================================================================= 1
    m.h(1, "1. GIỚI THIỆU CHUNG")
    m.h(2, "1.1. Phần mềm này để làm gì")
    m.p("Cổng thông tin điện tử là nơi tập trung của đơn vị để vừa TUYÊN TRUYỀN (tin tức, "
        "giáo dục chính trị, thông báo… cho mọi người xem) vừa CHỈ ĐẠO – TRIỂN KHAI nhiệm vụ có "
        "kiểm soát truy cập (chỉ tài khoản được cấp mới xem và trao đổi qua lại được).")
    m.bullets([
        "Khách truy cập trong mạng nội bộ: xem được tin tức, thông báo, văn bản ở mức CÔNG KHAI mà không cần đăng nhập.",
        "Tài khoản đã đăng nhập: xem thêm nội dung NỘI BỘ và dùng các chức năng theo quyền được cấp.",
        "Ban chỉ huy và các đơn vị: trao đổi, giao nhiệm vụ, nộp báo cáo, ký nhận công văn.",
    ])
    m.h(2, "1.2. Ai sẽ sử dụng")
    m.table(
        ["Đối tượng", "Vai trò tài khoản", "Làm được gì (tóm tắt)"],
        [["Ban chỉ huy Lữ đoàn (Lữ trưởng, Chính uỷ, các Phó…)", "Chỉ huy / Quản trị",
          "Toàn quyền: ban hành chỉ thị, duyệt & đăng mọi nội dung, quản lý tài khoản, dùng mọi kênh."],
         ["Cán bộ, sĩ quan, QNCN các phòng ban / tiểu đoàn / đại đội", "Cán bộ",
          "Đăng & biên tập Tin tức và Giáo dục chính trị; xem Chỉ thị; nếu được cấp thì dùng Kênh Chỉ đạo – Báo cáo."],
         ["Chiến sĩ", "Chiến sĩ (mặc định)",
          "Chỉ XEM tin tức, giáo dục chính trị, thông báo, chỉ thị liên quan. Không đăng, không sửa."],
         ["Người quản trị hệ thống (chủ đơn vị giữ)", "Quản trị (admin)",
          "Như Chỉ huy, và thêm: cấp tài khoản – phân quyền cho toàn Lữ đoàn, quản lý đơn vị."]],
        widths=[2.2, 1.4, 3.0],
    )
    m.h(2, "1.3. Cần gì để sử dụng")
    m.bullets([
        "Một máy tính hoặc điện thoại có trình duyệt web (khuyến nghị Microsoft Edge hoặc Google Chrome).",
        "Kết nối được vào mạng nội bộ của đơn vị (địa chỉ truy cập do bộ phận kỹ thuật cung cấp).",
        "Với tài khoản cá nhân: tên đăng nhập và mật khẩu do người quản trị / chỉ huy cấp.",
    ])
    m.note("Nếu đơn vị VỪA tiếp nhận phần mềm và chưa cài đặt: bộ phận kỹ thuật đọc Mục 3 trước "
           "(cài máy chủ, cơ sở dữ liệu, giao diện, thiết lập tài khoản ban đầu). Người dùng thông thường "
           "đọc tiếp từ Mục 4.")
    m.pagebreak()

    # ================================================================= 2
    m.h(1, "2. NHỮNG KHÁI NIỆM CẦN NẮM TRƯỚC")
    m.h(2, "2.1. Vai trò của tài khoản")
    m.p("“Vai trò” quyết định bạn được làm gì. Người quản trị / chỉ huy là người đặt vai trò cho từng tài khoản. "
        "Trên màn hình “Quản lý người dùng”, vai trò hiển thị đúng theo tên trong cột “Vai trò” dưới đây.")
    m.table(
        ["Tên hiển thị (trong hệ thống)", "Đối tượng thực tế", "Quyền chính"],
        [["Quản trị hệ thống", "Chủ đơn vị giữ tài khoản “admin” (và các tài khoản admin khác)",
          "Toàn quyền chỉ huy + độc quyền: cấp/thu “Quyền xem MẬT” và cờ Kênh Chỉ đạo, cấp lại mật khẩu, quản lý đơn vị, tạo tài khoản quản trị"],
         ["Lữ trưởng – Chính uỷ / Phó Lữ trưởng – Phó Chính uỷ / Chỉ huy đơn vị",
          "Ban chỉ huy Lữ đoàn và chỉ huy các đầu mối", "Toàn quyền chỉ huy: ban hành Chỉ thị, duyệt & đăng mọi nội dung, quản lý tài khoản"],
         ["Cá nhân", "Cán bộ, sĩ quan, QNCN các phòng ban / tiểu đoàn / đại đội được giao đăng nội dung",
          "Xem + đăng/sửa Tin tức và Giáo dục chính trị; xem Chỉ thị; nếu được bật cờ thì dùng Kênh Chỉ đạo – Báo cáo"],
         ["Người dùng", "Tài khoản đã kích hoạt nhưng chưa được giao việc đăng nội dung (mức mặc định khi tự đăng ký)",
          "Chỉ XEM nội bộ; không đăng, không sửa"]],
        widths=[2.0, 2.3, 2.3],
    )
    m.p("Trong tài liệu này, để gọn, các mục đôi khi viết tắt: “Chỉ huy” = nhóm toàn quyền chỉ huy (gồm cả Quản trị); "
        "“Cán bộ” = vai trò “Cá nhân” (được đăng nội dung); “Người dùng” = chỉ xem.", italic=True, color=GRAYTXT)
    m.h(2, "2.2. Ba bậc phân loại nội dung")
    m.p("Mỗi bài viết, văn bản, chỉ thị… có một “bậc phân loại” quy định ai được xem:")
    m.table(
        ["Bậc", "Ai xem được"],
        [["Công khai", "Bất kỳ ai trong mạng nội bộ, kể cả chưa đăng nhập"],
         ["Nội bộ", "Mọi tài khoản đã được kích hoạt"],
         ["MẬT", "Chỉ Chỉ huy/Quản trị HOẶC tài khoản được cấp “Quyền xem MẬT”"]],
        widths=[1.3, 5.3],
    )
    m.note("Chỉ Chỉ huy/Quản trị hoặc người có “Quyền xem MẬT” mới được TẠO nội dung bậc MẬT. "
           "Người không đủ quyền sẽ không nhìn thấy lựa chọn “MẬT” trong biểu mẫu.")
    m.h(2, "2.3. Đơn vị và hai kênh đặc biệt")
    m.bullets([
        "ĐƠN VỊ: mỗi tài khoản có thể được gán vào một đơn vị (Tiểu đoàn 1, Đại đội 5, Trạm bảo đảm, Ban chỉ huy Lữ đoàn, Cấp uỷ Lữ đoàn…). Việc gán do quản trị làm ở mục “Quản lý đơn vị” và “Quản lý người dùng”.",
        "KÊNH CHỈ ĐẠO – BÁO CÁO: nơi Ban chỉ huy và các đơn vị trao đổi 2 chiều và giao/nhận báo cáo. "
        "Chỉ tài khoản được quản trị bật cờ “Kênh Chỉ đạo” (hoặc là Chỉ huy/Quản trị) mới vào được. "
        "Tài khoản của đơn vị chỉ thấy phần việc của đơn vị mình.",
        "KÊNH CHỈ HUY (MẬT): dành riêng cho Ban chỉ huy Lữ đoàn và Cấp uỷ. Điều kiện vào là có “Quyền xem MẬT” "
        "(hoặc là Chỉ huy/Quản trị). Gồm: họp bàn nội bộ và sổ công văn mật.",
    ])
    m.h(2, "2.4. Bố cục màn hình")
    m.bullets([
        "Dải màu xanh phía trên: tên đơn vị và khẩu hiệu.",
        "Góc phải trên: tên tài khoản đang đăng nhập và nút “Đăng xuất”.",
        "Thanh menu ngang ngay dưới: danh sách chức năng. Bạn CHỈ thấy những mục mình có quyền dùng — "
        "vì vậy hai người khác vai trò sẽ thấy số mục khác nhau (xem Mục 18).",
        "Phần giữa: nội dung của trang đang mở.",
    ])
    m.pagebreak()

    # ================================================================= 3
    m.h(1, "3. KHI ĐƠN VỊ TIẾP NHẬN PHẦN MỀM — CÀI ĐẶT & CHUẨN BỊ KHAI THÁC")
    m.p("Mục này dành cho BỘ PHẬN KỸ THUẬT của đơn vị (trợ lý CNTT / người được giao "
        "quản trị hệ thống). Làm MỘT LẦN khi mới tiếp nhận phần mềm, theo đúng 8 bước dưới đây. "
        "Người dùng thông thường bỏ qua mục này và đọc từ Mục 4.")
    m.p("Toàn bộ lệnh gõ trong cửa sổ PowerShell (Windows). Ví dụ đường dẫn mã nguồn dùng "
        "d:\\Du_an_Lu_doan\\ludoan-main — thay bằng nơi đơn vị thực sự chép mã nguồn.")

    m.h(2, "3.1. Bộ bàn giao gồm những gì")
    m.bullets([
        "Thư mục backend\\  — phần MÁY CHỦ (xử lý dữ liệu, cấp tài khoản, lưu tệp).",
        "Thư mục frontend\\ — phần GIAO DIỆN người dùng nhìn thấy trên trình duyệt.",
        "Thư mục docs\\ — tài liệu hướng dẫn (bản .docx này) và hình minh hoạ.",
        "openapi.yaml và openapi.CHANGELOG.md — “hợp đồng API”, phục vụ bảo trì; không cần đụng tới khi vận hành.",
        "backend\\.env và frontend\\.env — file KHAI BÁO CẤU HÌNH (địa chỉ CSDL, mật khẩu, khoá bảo mật…). Sẽ sửa ở Bước 3 và Bước 6.",
    ])

    m.h(2, "3.2. Chuẩn bị máy chủ và phần mềm nền")
    m.table(
        ["Thành phần", "Yêu cầu tối thiểu", "Ghi chú"],
        [["Máy chủ", "1 máy chạy Windows 10/11 hoặc Windows Server 2016+ (hoặc Linux)",
          "Luôn bật, nối mạng nội bộ đơn vị, ĐẶT ĐỊA CHỈ IP TĨNH (vd 192.168.1.10)."],
         ["Python", "Phiên bản 3.11 trở lên", "Tải ở python.org. Khi cài TÍCH ô “Add python.exe to PATH”."],
         ["MySQL", "MySQL 8.0 (hoặc MariaDB 10.5+)", "Nhớ mật khẩu tài khoản root khi cài."],
         ["Node.js", "Phiên bản 18 hoặc 20", "CHỈ cần để đóng gói giao diện (Bước 6). Xong có thể gỡ."],
         ["Trình duyệt máy trạm", "Microsoft Edge hoặc Google Chrome bản mới", "Máy người dùng cuối."],
         ["Ổ đĩa trống", "≥ 5 GB", "Dự phòng cho tệp đính kèm, cơ sở dữ liệu và bản sao lưu (lớn dần theo thời gian)."]],
        widths=[1.5, 2.6, 2.5],
    )

    m.h(2, "3.3. Bước 1 — Tạo cơ sở dữ liệu MySQL")
    m.steps([
        "Cài và khởi động MySQL. Mở công cụ dòng lệnh MySQL, đăng nhập bằng tài khoản root.",
        "Chạy lần lượt 4 câu lệnh sau (giữ đúng tên “ludoan_db”, “quynh_user” cho khớp file .env mẫu; "
        "thay chuỗi trong dấu nháy của IDENTIFIED BY bằng một mật khẩu mạnh do đơn vị đặt):",
    ])
    m.bullets([
        "CREATE DATABASE ludoan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "CREATE USER 'quynh_user'@'%' IDENTIFIED BY 'DAT_MAT_KHAU_MANH_O_DAY';",
        "GRANT ALL PRIVILEGES ON ludoan_db.* TO 'quynh_user'@'%';",
        "FLUSH PRIVILEGES;",
    ])
    m.p("Ghi lại 3 thông tin: TÊN CSDL (ludoan_db), TÊN NGƯỜI DÙNG (quynh_user), MẬT KHẨU vừa đặt — "
        "sẽ điền vào .env ở Bước 3.")
    m.note("Nếu đơn vị đã có sẵn CSDL từ bản chạy thử trước đó (đã có dữ liệu): BỎ QUA bước tạo mới này, "
           "chuyển thẳng tới Bước 4, phần B (nâng cấp cấu trúc bảng).")

    m.h(2, "3.4. Bước 2 — Cài đặt phần Máy chủ (backend)")
    m.steps([
        "Mở PowerShell, chuyển vào thư mục backend:   cd d:\\Du_an_Lu_doan\\ludoan-main\\backend",
        "Tạo môi trường Python riêng cho phần mềm:   python -m venv venv",
        "Cài thư viện cần dùng:   venv\\Scripts\\pip install -r requirements.txt",
        "Chờ tải xong (vài phút). KHÔNG có dòng chữ màu đỏ báo lỗi là đạt.",
    ])
    m.note("Máy chủ không nối được Internet: chép sẵn thư mục venv đã cài đầy đủ từ một máy khác có CÙNG "
           "phiên bản Python và Windows; hoặc tải trước các gói .whl rồi cài offline: "
           "venv\\Scripts\\pip install --no-index --find-links=<thư mục chứa .whl> -r requirements.txt")

    m.h(2, "3.5. Bước 3 — Khai báo file cấu hình backend\\.env")
    m.p("Mở file backend\\.env bằng Notepad. Đây là nơi DUY NHẤT chứa mật khẩu và khoá bảo mật — "
        "tuyệt đối không sửa các thông tin này trong mã nguồn. Sửa theo bảng:")
    m.table(
        ["Dòng trong .env", "Ý nghĩa", "Phải làm gì"],
        [["MYSQL_HOST / MYSQL_PORT", "Địa chỉ và cổng máy MySQL", "Để localhost / 3306 nếu MySQL cùng máy với backend."],
         ["MYSQL_DATABASE", "Tên cơ sở dữ liệu", "Đúng tên đã tạo ở Bước 1 (ludoan_db)."],
         ["MYSQL_USER / MYSQL_PASSWORD", "Tài khoản truy cập CSDL", "Đúng tài khoản và mật khẩu đã tạo ở Bước 1."],
         ["DATABASE_URL", "Chuỗi kết nối đầy đủ", "Nếu mật khẩu có ký tự đặc biệt phải mã hoá: @ → %40, # → %23, / → %2F. "
          "KHÔNG chắc thì XOÁ TRỐNG dòng này — hệ thống tự dựng chuỗi từ các dòng MYSQL_* ở trên."],
         ["JWT_SECRET_KEY", "Khoá ký phiên đăng nhập", "BẮT BUỘC đổi thành một chuỗi ngẫu nhiên dài ≥ 40 ký tự, "
          "giữ bí mật. Đổi khoá này về sau sẽ khiến mọi người phải đăng nhập lại."],
         ["JWT_EXPIRE_MINUTES", "Thời hạn một phiên đăng nhập (phút)", "1440 = 1 ngày. Tuỳ đơn vị quy định."],
         ["MAX_UPLOAD_MB", "Dung lượng tối đa mỗi tệp tải lên", "Mặc định 50."],
         ["UPLOAD_DIR", "Thư mục lưu tệp đính kèm", "Để mặc định storage/uploads."],
         ["EXTRA_CORS_ORIGINS", "Địa chỉ giao diện được phép gọi máy chủ", "Các dải LAN 10.x, 192.168.x, 172.16–31.x "
          "đã mở sẵn. Chỉ thêm vào đây nếu máy chủ web dùng địa chỉ ngoài các dải đó (phân tách bằng dấu phẩy)."],
         ["SYSTEM_ADMIN_USERNAME / SYSTEM_ADMIN_PASSWORD", "Tài khoản quản trị tạo sẵn ở lần chạy đầu",
          "Có thể để admin / admin — hệ thống bắt đổi mật khẩu ngay lần đăng nhập đầu tiên."]],
        widths=[1.9, 2.1, 3.0],
    )
    m.note("Sau khi sửa xong: lưu file, giữ MỘT BẢN SAO ở nơi an toàn tách khỏi máy chủ. "
           "Không đưa file .env lên kho mã nguồn dùng chung.")

    m.h(2, "3.6. Bước 4 — Tạo bảng và dữ liệu khởi tạo")
    m.p("Có hai trường hợp — chọn đúng một:")
    m.p("A. CÀI ĐẶT MỚI HOÀN TOÀN (cơ sở dữ liệu vừa tạo, còn rỗng):", bold=True)
    m.bullets([
        "Không cần chạy thêm lệnh nào. Ngay lần đầu khởi động máy chủ (Bước 5), hệ thống TỰ tạo toàn bộ bảng, "
        "TỰ tạo tài khoản quản trị, và TỰ nạp 10 đơn vị chuẩn: Ban chỉ huy Lữ đoàn, Cấp uỷ – Đảng bộ Lữ đoàn, "
        "Phòng Tham mưu, Phòng Chính trị, Phòng Hậu cần – Kỹ thuật, Tiểu đoàn 1, Tiểu đoàn 2, Đại đội 5, "
        "Trạm bảo đảm, Trung tâm 2.",
    ])
    m.p("B. NÂNG CẤP TỪ CSDL BẢN CHẠY THỬ CŨ (đã có dữ liệu):", bold=True)
    m.p("Trong thư mục backend, chạy lần lượt các lệnh sau, ĐÚNG THỨ TỰ (chạy lại nhiều lần không hỏng, không mất dữ liệu):")
    m.steps([
        "venv\\Scripts\\python scripts\\migrate_posts_approval.py",
        "venv\\Scripts\\python scripts\\migrate_access_tiers.py",
        "venv\\Scripts\\python scripts\\migrate_org_and_channels.py",
        "(không bắt buộc) venv\\Scripts\\python scripts\\seed_units.py  — bổ sung các đơn vị chuẩn còn thiếu.",
        "(không bắt buộc) venv\\Scripts\\python scripts\\seed_admin.py  — tạo / xác nhận tài khoản quản trị hệ thống.",
    ])
    m.note("3 lệnh “migrate” chỉ THÊM cột / bảng, KHÔNG xoá dữ liệu. Nếu báo “column already exists”, "
           "“Duplicate column” hay tương tự nghĩa là đã chạy trước đó rồi — bỏ qua, chạy tiếp lệnh sau.")

    m.h(2, "3.7. Bước 5 — Khởi động phần Máy chủ")
    m.steps([
        "Trong thư mục backend, chạy:   venv\\Scripts\\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000",
        "Thấy dòng “Application startup complete” và “Uvicorn running on http://0.0.0.0:8000” là máy chủ đã chạy. "
        "GIỮ NGUYÊN cửa sổ PowerShell này (đóng lại là máy chủ tắt).",
        "Kiểm tra tại chỗ: trên chính máy chủ mở trình duyệt vào http://127.0.0.1:8000/ — phải thấy {\"status\":\"ok\"…}. "
        "Vào http://127.0.0.1:8000/docs để xem danh sách API.",
        "Kiểm tra từ máy khác: http://<IP máy chủ>:8000/ (vd http://192.168.1.10:8000/). Nếu không vào được "
        "→ mở cổng 8000 (inbound) trên Windows Firewall của máy chủ.",
    ])
    m.p("Để máy chủ tự chạy nền và tự bật lại khi khởi động Windows (không phải mở PowerShell thủ công), "
        "chọn một cách:")
    m.bullets([
        "Task Scheduler (Bộ lập lịch tác vụ): tạo tác vụ chạy lệnh uvicorn ở trên, kích hoạt lúc "
        "“When the computer starts”, chọn “Run whether user is logged on or not”.",
        "Công cụ NSSM: đăng ký lệnh uvicorn thành một Windows Service để hệ điều hành tự quản lý.",
        "Trên Linux: tạo một unit systemd.",
    ])

    m.h(2, "3.8. Bước 6 — Cài đặt phần Giao diện (frontend)")
    m.steps([
        "Mở một cửa sổ PowerShell mới, vào thư mục frontend:   cd d:\\Du_an_Lu_doan\\ludoan-main\\frontend",
        "Sửa file frontend\\.env: dòng VITE_API_BASE_URL đặt bằng http://<IP máy chủ>:8000 (đúng địa chỉ ở Bước 5). "
        "Nếu giao diện đặt cùng máy với máy chủ, có thể để http://127.0.0.1:8000.",
        "Cài thư viện:   npm install",
        "Đóng gói giao diện:   npm run build   → tạo ra thư mục frontend\\dist",
        "Đưa TOÀN BỘ nội dung thư mục dist lên một máy chủ web tĩnh để phục vụ người dùng: dùng IIS (Windows) "
        "trỏ site vào thư mục dist, hoặc nginx; cách nhanh để dùng thử: npm run preview -- --host --port 5173 "
        "(giữ cửa sổ mở).",
        "Người dùng truy cập địa chỉ máy chủ web đó (vd http://192.168.1.10 hoặc http://192.168.1.10:5173).",
    ])
    m.note("Mỗi lần đổi VITE_API_BASE_URL trong frontend\\.env PHẢI chạy lại npm run build và cập nhật lại thư mục "
           "dist — địa chỉ máy chủ được “nướng” vào lúc build, không đọc lại khi chạy.")
    m.note("Nếu phục vụ bằng IIS / nginx: cấu hình “fallback” mọi đường dẫn không trỏ tới tệp thật về /index.html. "
           "Thiếu bước này, người dùng bấm F5 (tải lại) ở một trang con sẽ gặp lỗi 404.")

    m.h(2, "3.9. Bước 7 — Đăng nhập lần đầu và thiết lập ban đầu (BẮT BUỘC)")
    m.p("Làm theo đúng thứ tự danh mục dưới đây, tất cả trên giao diện web — không cần đụng vào cơ sở dữ liệu.")
    m.steps([
        "Vào địa chỉ giao diện, bấm “Đăng nhập”, nhập admin / admin (hoặc giá trị SYSTEM_ADMIN_* đã đặt trong .env).",
        "Hệ thống bắt đổi mật khẩu: đặt MẬT KHẨU QUẢN TRỊ MỚI thật mạnh; ghi vào sổ bàn giao và cất giữ theo chế độ mật.",
        "Vào “Quản lý đơn vị”: kiểm tra đủ 10 đơn vị chuẩn; thêm / sửa / ẩn cho khớp biên chế thực tế của đơn vị.",
        "Vào “Quản lý người dùng” → tạo tài khoản cho Ban chỉ huy thật (Lữ trưởng, Chính uỷ, các Phó): "
        "vai trò “Chỉ huy”, gán đơn vị “Ban chỉ huy Lữ đoàn”.",
        "Cấp “Quyền xem MẬT” cho các tài khoản thuộc Ban chỉ huy và Cấp uỷ (điều kiện vào Kênh chỉ huy MẬT).",
        "Tạo tài khoản cho cán bộ các phòng / ban / tiểu đoàn / đại đội: vai trò “Cán bộ”, gán ĐÚNG đơn vị của họ.",
        "Với cán bộ là đầu mối nhận nhiệm vụ / báo cáo của đơn vị: tích thêm ô “Kênh Chỉ đạo”.",
        "Tạo tài khoản cho chiến sĩ (hoặc mở chức năng tự đăng ký rồi kích hoạt dần): để vai trò mặc định “Chiến sĩ”.",
        "Mỗi tài khoản mới sẽ bị buộc đổi mật khẩu ở lần đăng nhập đầu — phổ biến điều này cho người dùng.",
        "Tự kiểm tra một vòng: đăng nhập 1 tài khoản Cán bộ → đăng thử 1 tin tức; đăng nhập 1 tài khoản Chỉ huy → "
        "duyệt tin đó; đăng 1 thông báo công khai rồi mở trang công khai (chưa đăng nhập) để xác nhận hiển thị.",
        "Phổ biến cho toàn đơn vị: địa chỉ truy cập, cách nhận tài khoản, và nội dung từ Mục 4 trở đi của tài liệu này.",
    ])

    m.h(2, "3.10. Bước 8 — Sao lưu và bảo trì định kỳ")
    m.bullets([
        "Sao lưu CƠ SỞ DỮ LIỆU hằng ngày (tối thiểu hằng tuần): trên máy chủ chạy "
        "mysqldump -u quynh_user -p ludoan_db > ludoan_db_YYYYMMDD.sql ; cất bản sao sang ổ / khay khác.",
        "Sao lưu thư mục backend\\storage\\uploads (toàn bộ ảnh, văn bản, tệp đính kèm) cùng nhịp với CSDL.",
        "Giữ bản sao backend\\.env và frontend\\.env ở nơi an toàn, tách khỏi máy chủ.",
        "KHÔNG sửa trực tiếp dữ liệu trong MySQL — mọi thao tác làm qua giao diện để hệ thống kiểm soát ràng buộc.",
        "Khi lên phiên bản mới: sao lưu trước → chép mã nguồn mới đè lên → chạy lại Bước 2 (pip install) → "
        "chạy các script migrate mới nếu bản giao hàng có kèm → khởi động lại máy chủ → build lại giao diện.",
        "Định kỳ kiểm tra dung lượng ổ đĩa (tệp đính kèm sẽ lớn dần theo thời gian).",
    ])

    m.h(2, "3.11. Sự cố khi cài đặt / khởi động máy chủ — tự khắc phục")
    m.table(
        ["Hiện tượng / thông báo", "Nguyên nhân thường gặp", "Cách xử lý"],
        [["ModuleNotFoundError: No module named 'app' khi chạy uvicorn", "Đang đứng sai thư mục",
          "cd vào đúng thư mục backend rồi chạy lại lệnh."],
         ["ModuleNotFoundError tên thư viện khác (vd 'multipart', 'fastapi', 'jose')", "Chưa cài / cài thiếu thư viện",
          "Chạy lại: venv\\Scripts\\pip install -r requirements.txt"],
         ["'uvicorn' / 'python' is not recognized…", "Chưa dùng Python trong venv, hoặc Python không có trong PATH",
          "Gọi kèm đường dẫn: venv\\Scripts\\python -m uvicorn …  Cài lại Python có tích “Add to PATH”."],
         ["(2003, \"Can't connect to MySQL server…\")", "MySQL chưa chạy, hoặc sai host / port",
          "Bật dịch vụ MySQL; kiểm tra lại MYSQL_HOST và MYSQL_PORT trong .env."],
         ["(1045, \"Access denied for user…\")", "Sai MYSQL_USER / MYSQL_PASSWORD, hoặc chuỗi DATABASE_URL sai",
          "Sửa .env. Nếu mật khẩu có ký tự đặc biệt: mã hoá trong DATABASE_URL (@→%40) hoặc XOÁ TRỐNG dòng DATABASE_URL."],
         ["(1049, \"Unknown database 'ludoan_db'\")", "Chưa tạo cơ sở dữ liệu", "Làm lại Bước 1 (CREATE DATABASE…)."],
         ["Báo cần 'cryptography' hoặc lỗi 'caching_sha2_password'", "Thiếu thư viện mã hoá, hoặc plugin xác thực MySQL",
          "Cài đủ requirements (đã có sẵn 'cryptography'); hoặc trên MySQL: "
          "ALTER USER 'quynh_user'@'%' IDENTIFIED WITH mysql_native_password BY '<mật khẩu>';"],
         ["[Errno 10048] … address … :8000 … (cổng 8000 đã bị chiếm)", "Tiến trình khác (hoặc máy chủ cũ chưa tắt) đang dùng cổng 8000",
          "Tắt tiến trình cũ; hoặc chạy cổng khác --port 8080 (nhớ sửa VITE_API_BASE_URL và build lại giao diện)."],
         ["pydantic … validation error … Field required (MYSQL_HOST…)", "Không thấy file .env, hoặc thiếu dòng bắt buộc",
          "Chạy uvicorn TỪ trong thư mục backend (nơi có .env); bổ sung đủ MYSQL_HOST / MYSQL_DATABASE / MYSQL_USER / "
          "MYSQL_PASSWORD / JWT_SECRET_KEY."],
         ["Máy khác trong mạng không mở được http://<IP>:8000", "Tường lửa chặn, hoặc chạy uvicorn thiếu --host 0.0.0.0",
          "Thêm --host 0.0.0.0 vào lệnh; mở cổng 8000 (inbound) trên Windows Firewall."],
         ["Log khởi động: “Khong the khoi tao tai khoan admin he thong”", "CSDL cũ chưa có các cột mới (is_system, must_change_password)",
          "Chạy scripts\\migrate_org_and_channels.py rồi khởi động lại máy chủ."],
         ["npm run build báo lỗi phiên bản Node", "Node.js quá cũ", "Cài Node.js 18 hoặc 20, chạy lại npm install rồi npm run build."],
         ["Giao diện mở ra TRẮNG TRANG; F12 → Console báo lỗi tải tệp .js", "Máy chủ web chưa cấu hình fallback về index.html, hoặc gốc site trỏ sai",
          "Cấu hình SPA fallback (xem Bước 6); kiểm tra gốc site trỏ đúng vào thư mục dist."],
         ["Đăng nhập trên giao diện báo lỗi mạng / CORS (backend vẫn chạy)", "VITE_API_BASE_URL sai, hoặc địa chỉ giao diện ngoài dải cho phép",
          "Sửa frontend\\.env cho đúng IP:cổng máy chủ, build lại; thêm địa chỉ giao diện vào EXTRA_CORS_ORIGINS trong "
          "backend\\.env rồi khởi động lại backend."],
         ["Tệp / ảnh tải lên xong nhưng mở lại bị 404", "Thư mục storage/uploads bị xoá / di chuyển, hoặc đổi UPLOAD_DIR mà chưa chuyển dữ liệu",
          "Giữ nguyên UPLOAD_DIR; khôi phục thư mục storage/uploads từ bản sao lưu."],
         ["Nhiệm vụ hiển thị “Quá hạn” sai; phiên đăng nhập hết hạn quá nhanh", "Đồng hồ máy chủ sai giờ / sai múi giờ",
          "Chỉnh lại ngày giờ và múi giờ (GMT+7) trên máy chủ; bật đồng bộ thời gian (NTP)."]],
        widths=[2.3, 2.0, 2.7],
    )
    m.note("Lỗi không có trong bảng, hoặc đã xử lý mà vẫn còn: chụp lại TOÀN BỘ các dòng chữ màu đỏ trong cửa sổ "
           "PowerShell (hoặc log máy chủ) và liên hệ đơn vị bàn giao phần mềm.")
    m.pagebreak()

    # ================================================================= 4
    m.h(1, "4. BẮT ĐẦU SỬ DỤNG")
    m.h(2, "4.1. Đăng nhập")
    m.figure("01_login", "Màn hình đăng nhập")
    m.steps([
        "Mở trình duyệt, gõ địa chỉ cổng thông tin của đơn vị. Nếu là khách, trang công khai hiện ra — bấm “Đăng nhập” ở góc phải.",
        "Ô (1) — nhập TÊN ĐĂNG NHẬP (chữ thường, không dấu, ví dụ: canbo.td1).",
        "Ô (2) — nhập MẬT KHẨU được cấp.",
        "Bấm nút (3) “Đăng nhập”.",
    ])
    m.note("Sai tên/mật khẩu → báo “Invalid username or password”. Tài khoản mới đăng ký chưa được duyệt → "
           "báo “Tài khoản chưa được kích hoạt — vui lòng chờ chỉ huy đơn vị duyệt”. Khi đó liên hệ người quản trị / chỉ huy.")
    m.h(2, "4.2. Đổi mật khẩu lần đầu (bắt buộc)")
    m.p("Tài khoản do quản trị cấp (hoặc vừa được cấp lại mật khẩu) sẽ bị đưa thẳng tới màn hình đổi mật khẩu "
        "và KHÔNG vào được chức năng nào cho tới khi đổi xong.")
    m.figure("02_doi_mat_khau", "Màn hình bắt buộc đổi mật khẩu lần đầu")
    m.steps([
        "Ô (1) — nhập lại MẬT KHẨU HIỆN TẠI (mật khẩu vừa được cấp).",
        "Ô (2) — nhập MẬT KHẨU MỚI. Quy định: tối thiểu 8 ký tự, có cả chữ và số. Nên đặt khó đoán.",
        "Ô (3) — gõ lại đúng mật khẩu mới để xác nhận.",
        "Bấm (4) “Đổi mật khẩu & tiếp tục”. Hệ thống tự đăng nhập lại và đưa bạn vào Bảng tin.",
    ])
    m.note("Riêng tài khoản “admin” của hệ thống được miễn quy định độ dài/độ mạnh — nhưng chủ đơn vị vẫn nên "
           "đặt mật khẩu mạnh và giữ bí mật.")
    m.h(2, "4.3. Đăng xuất")
    m.p("Bấm nút “Đăng xuất” ở góc phải trên. Luôn đăng xuất khi rời máy dùng chung.")
    m.h(2, "4.4. Tự đăng ký (nếu được mở)")
    m.steps([
        "Ở trang đăng nhập bấm “Đăng ký”.",
        "Nhập tên đăng nhập (chữ thường, ≥ 3 ký tự), mật khẩu (≥ 8 ký tự có cả chữ và số), họ tên.",
        "Gửi đăng ký. Tài khoản ở trạng thái “chờ duyệt”, CHƯA đăng nhập được.",
        "Báo cho chỉ huy/quản trị để được kích hoạt và phân quyền.",
    ])
    m.h(2, "4.5. Quên mật khẩu / bị khoá")
    m.p("Hệ thống nội bộ không có chức năng tự lấy lại mật khẩu. Liên hệ người quản trị / chỉ huy để được "
        "“Cấp lại mật khẩu”. Sau khi được cấp lại, bạn đăng nhập bằng mật khẩu tạm và làm lại bước 4.2.")
    m.pagebreak()

    # ================================================================= 5
    m.h(1, "5. TRANG CÔNG KHAI & BẢNG TIN")
    m.h(2, "5.1. Trang công khai (không cần đăng nhập)")
    m.figure("03_trang_cong_khai", "Trang công khai cho khách trong mạng nội bộ")
    m.bullets([
        "(1) Nút “Đăng nhập” ở góc phải để vào hệ thống nội bộ.",
        "(2) Khu Tin tức – Hoạt động: các bài đã duyệt ở bậc Công khai.",
        "(3) Thông báo và văn bản được đánh dấu công khai.",
    ])
    m.h(2, "5.2. Bảng tin (sau khi đăng nhập)")
    m.figure("04_bang_tin", "Bảng tin nội bộ — trang chính sau khi đăng nhập")
    m.bullets([
        "(1) Các ô tóm tắt: tin tức mới, giáo dục chính trị, chỉ thị, thông báo mới nhất. Bấm vào để mở nhanh.",
        "(2) Thanh menu: toàn bộ chức năng bạn được phép dùng. Nếu không thấy mục nào đó nghĩa là bạn chưa được cấp quyền.",
    ])
    m.pagebreak()

    # ================================================================= 6
    m.h(1, "6. TIN TỨC – HOẠT ĐỘNG ĐƠN VỊ")
    m.p("Ai xem: mọi người (bài đã duyệt, đúng bậc phân loại). Ai đăng/sửa: Cán bộ và Chỉ huy.")
    m.figure("05_tin_tuc", "Màn hình Tin tức – danh sách và biểu mẫu soạn bài")
    m.h(2, "6.1. Xem tin tức")
    m.steps(["Vào menu “Tin tức – Hoạt động”.", "Bấm một bài trong danh sách (1) để đọc nội dung."])
    m.h(2, "6.2. Đăng bài mới (Cán bộ / Chỉ huy)")
    m.steps([
        "Ở biểu mẫu bên phải, ô (2) nhập TIÊU ĐỀ.",
        "Chọn DANH MỤC: Huấn luyện / Dân vận / Khen thưởng / Gương người tốt.",
        "Ô (3) chọn BẬC PHÂN LOẠI (Công khai / Nội bộ / MẬT). Nếu không đủ quyền sẽ không có lựa chọn MẬT.",
        "Ô (4) nhập NỘI DUNG bài viết (có thể nhiều đoạn).",
        "Bấm (5) “Lưu bài”. Nếu cần ảnh, bấm “Tải ảnh bìa” và chọn tệp ảnh.",
    ])
    m.note("Luồng duyệt: Cán bộ đăng → bài ở trạng thái “Chờ duyệt”, chưa hiển thị công khai. "
           "Chỉ huy đăng → “Đã duyệt” ngay. Cán bộ sửa lại bài đã duyệt/bị trả lại → bài tự quay về “Chờ duyệt”.")
    m.h(2, "6.3. Duyệt / trả lại bài (chỉ Chỉ huy)")
    m.figure("06_duyet_bai", "Chỉ huy duyệt bài chờ duyệt")
    m.steps([
        "Mở bài đang ở trạng thái “Chờ duyệt” ((1) trong danh sách).",
        "Nếu cần góp ý, nhập vào ô (2) “Ghi chú duyệt / lý do trả lại”.",
        "Bấm (3) “Duyệt đăng” để công bố, hoặc “Trả lại tác giả” để tác giả sửa.",
    ])
    m.pagebreak()

    # ================================================================= 7
    m.h(1, "7. GIÁO DỤC CHÍNH TRỊ")
    m.p("Ai xem: mọi tài khoản đã đăng nhập. Ai đăng/sửa: Cán bộ và Chỉ huy.")
    m.figure("07_giao_duc", "Soạn tài liệu giáo dục chính trị")
    m.steps([
        "Vào menu “Giáo dục chính trị”.",
        "(1) Nhập TIÊU ĐỀ.",
        "(2) Chọn DANH MỤC (Học tập chính trị – quân sự / Tuyên truyền / Pháp luật biên giới / Lịch sử – truyền thống).",
        "(3) Nếu là nội dung theo kỳ, nhập KỲ ÁP DỤNG (ví dụ: “Tuần 35/2026”).",
        "(4) Nhập NỘI DUNG. Có thể dán đường dẫn tài liệu đính kèm.",
        "(5) Bấm “Lưu”.",
    ])
    m.pagebreak()

    # ================================================================= 8
    m.h(1, "8. THÔNG BÁO – LỊCH TRỰC KÍP")
    m.p("Ai xem: thông báo công khai thì mọi người; còn lại cần đăng nhập. Lịch trực cần đăng nhập. "
        "Ai đăng/sửa: Cán bộ và Chỉ huy.")
    m.figure("08_thong_bao", "Đăng thông báo nội bộ")
    m.steps([
        "Vào menu “Thông báo – Lịch trực”.",
        "(1) Nhập TIÊU ĐỀ và (2) chọn MỨC ƯU TIÊN (Thấp / Bình thường / Cao / Khẩn).",
        "(3) Nhập NỘI DUNG.",
        "Tích “Ghim lên đầu” nếu muốn thông báo luôn nằm trên cùng; tích “Công khai” nếu cho khách xem.",
        "Bấm “Lưu”. Danh sách sắp xếp: ghim → ưu tiên → mới nhất.",
    ])
    m.h(2, "8.1. Lịch trực – Kíp trực")
    m.figure("08b_lich_truc", "Trang Lịch trực – Kíp trực (4 thẻ: biểu trực tuần / kíp trực ngày / lập & duyệt / sổ bàn giao ca)")
    m.bullets([
        "Thẻ “Biểu trực tuần”: xem toàn Lữ đoàn hoặc theo khối/đơn vị; chọn tuần bằng nút “Tuần trước / Tuần này / Tuần sau”; "
        "chú giải màu theo 7 loại trực (chỉ huy, ban tác chiến, ban nội vụ, chuyên môn, ca kíp, bảo vệ – vệ binh, khác). "
        "Chỉ bảng đã duyệt mới lên bảng tổng hợp chung. Bấm “In biểu trực” để in.",
        "Thẻ “Kíp trực ngày”: xem chi tiết kíp trực của một ngày cụ thể, gom theo đơn vị, kèm tổng quân số có mặt / biên chế.",
        "Thẻ “Lập & duyệt bảng trực”: trực ban đơn vị (thường là Phòng Tham mưu) lập bảng trực tuần cho đơn vị mình, "
        "thêm từng dòng ca trực rồi bấm “Gửi duyệt”. Luồng: Nháp → Chờ duyệt → Đã duyệt / Trả lại (kèm lý do) → có thể Mở lại. "
        "Mỗi đơn vị chỉ có một bảng cho mỗi tuần. Chỉ huy Lữ đoàn bấm “Phê duyệt lịch trực” hoặc “Trả lại / Yêu cầu Tham mưu sửa”.",
    ])
    m.h(2, "8.2. Bàn giao ca trực điện tử (sổ nhật ký kíp trực)")
    m.figure("08b_lich_truc", "Thẻ “Sổ bàn giao & Nhật ký kíp trực” trong trang Lịch trực")
    m.p("Mỗi biên bản bàn giao gắn với một dòng ca trực trong biểu trực tuần. Quy trình 3 bước:")
    m.steps([
        "Kíp trước lập biên bản: tình hình quân số; tình hình khí tài thông tin liên lạc – vũ khí trang bị; "
        "nhật ký các sự vụ / mệnh lệnh nhận trong ca; nhiệm vụ còn dở dang bàn giao ca sau theo dõi.",
        "Kíp sau đối soát thực tế rồi ký nhận điện tử: chọn “Đã nhận” hoặc “Có kiến nghị” (kèm ghi chú phản hồi).",
        "Chỉ huy ca trực kiểm tra và ghi ý kiến chỉ đạo vào sổ.",
    ])
    m.bullets([
        "Trạng thái mỗi biên bản: Chờ nhận / Đã nhận / Có kiến nghị.",
        "Tất cả lưu vết thời gian, người giao – người nhận; tra cứu lại theo khoảng ngày / đơn vị / trạng thái.",
    ])
    m.h(2, "8.3. Danh bạ điện thoại")
    m.figure("08c_danh_ba", "Trang Danh bạ điện thoại (nhập từ file Excel/CSV)")
    m.steps([
        "Vào menu Bản tin → “Danh bạ điện thoại”.",
        "Bấm “Nhập danh bạ”, chọn file Excel (.xlsx) hoặc .csv của đơn vị / Bộ đội Biên phòng / toàn quân.",
        "Hệ thống giữ NGUYÊN mọi cột của file. Dùng ô tìm kiếm để tra nhanh trên tất cả các trường (tên, đơn vị, chức danh, số máy…).",
        "Có thể nhập nhiều bộ danh bạ; chọn bộ ở danh sách bên trái để tra cứu.",
    ])
    m.pagebreak()

    # ================================================================= 9
    m.h(1, "9. VĂN BẢN – TÀI LIỆU – BIỂU MẪU")
    m.p("Ai xem: tài liệu công khai thì mọi người; còn lại cần đăng nhập (đúng bậc phân loại). "
        "Ai đăng/sửa: Cán bộ và Chỉ huy.")
    m.figure("09_van_ban", "Tải lên văn bản / tài liệu")
    m.steps([
        "Vào menu “Văn bản – Tài liệu”.",
        "(1) Nhập TIÊU ĐỀ.",
        "(2) Chọn CHUYÊN MỤC (Biểu mẫu / Hướng dẫn / Quy chế – quy định / Kế hoạch / Báo cáo / Văn bản chỉ đạo).",
        "(3) Chọn BẬC PHÂN LOẠI.",
        "(4) Bấm “Chọn tệp” và chọn file .pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx (dung lượng trong giới hạn cho phép).",
        "Bấm “Lưu”. Người xem bấm “Tải về” để lấy tệp (hệ thống kiểm tra quyền trước khi cho tải).",
    ])
    m.pagebreak()

    # ================================================================= 10
    m.h(1, "10. CHỈ THỊ – NHIỆM VỤ")
    m.p("Ai xem: mọi tài khoản đã đăng nhập thấy chỉ thị “Đã ban hành”. Ai ban hành: CHỈ Chỉ huy/Quản trị.")
    m.figure("09b_chi_thi", "Ban hành chỉ thị")
    m.h(2, "10.1. Người nhận: xem và “Tôi đã tiếp thu”")
    m.steps([
        "Vào menu “Chỉ thị – Nhiệm vụ”, mở chỉ thị để đọc.",
        "Bấm nút “Tôi đã tiếp thu”. Nút này bấm một lần là đủ (bấm lại không sao).",
    ])
    m.h(2, "10.2. Chỉ huy: ban hành và theo dõi quán triệt")
    m.steps([
        "(1) Nhập TIÊU ĐỀ và NỘI DUNG chỉ thị.",
        "(2) Chọn TRẠNG THÁI: “Bản nháp” (chỉ chỉ huy thấy) hoặc “Đã ban hành” (mọi người thấy).",
        "(3) Chọn BẬC PHÂN LOẠI.",
        "(4) Bấm “Lưu”.",
        "Mở chỉ thị đã ban hành để xem danh sách “Đã tiếp thu” / “Chưa tiếp thu” theo từng tài khoản.",
    ])
    m.pagebreak()

    # ================================================================= 11
    m.h(1, "11. KÊNH CHỈ ĐẠO – BÁO CÁO: LUỒNG TRAO ĐỔI")
    m.p("Điều kiện: được quản trị bật cờ “Kênh Chỉ đạo”, hoặc là Chỉ huy/Quản trị. "
        "Ban chỉ huy thấy luồng của MỌI đơn vị; tài khoản đơn vị chỉ thấy luồng của đơn vị mình.")
    m.figure("10_chi_dao_luong", "Kênh Chỉ đạo – Báo cáo, phần luồng trao đổi")
    m.steps([
        "Vào menu “Chỉ đạo – Báo cáo”.",
        "(1) Tạo luồng: gõ tiêu đề vào ô trên cùng rồi bấm “Tạo luồng”. Ban chỉ huy chọn thêm đơn vị; "
        "tài khoản đơn vị thì luồng tự thuộc về đơn vị mình.",
        "(2) Bấm một luồng ở danh sách bên trái để mở nội dung.",
        "(3) Gõ nội dung trao đổi / báo cáo vào ô soạn tin.",
        "(4) Bấm “Chọn tệp” nếu cần gửi kèm file (ảnh hoặc .pdf/.doc/.docx…), rồi bấm “Gửi”.",
    ])
    m.bullets([
        "Số màu đỏ cạnh tên luồng là số tin CHƯA ĐỌC. Mở luồng ra là tự đánh dấu đã đọc.",
        "Chỉ huy có thể “Đóng luồng” khi việc đã xong; luồng đã đóng thì không gửi thêm được (mở lại được).",
    ])
    m.pagebreak()

    # ================================================================= 12
    m.h(1, "12. KÊNH CHỈ ĐẠO – BÁO CÁO: GIAO NHIỆM VỤ & NỘP BÁO CÁO")
    m.p("Giao / sửa / huỷ nhiệm vụ và duyệt báo cáo: CHỈ Chỉ huy/Quản trị. "
        "Nộp báo cáo tiến độ: tài khoản thuộc đơn vị được giao.")
    m.figure("11_giao_nhiem_vu", "Giao nhiệm vụ và bảng theo dõi tiến độ")
    m.h(2, "12.1. Chỉ huy giao nhiệm vụ")
    m.steps([
        "Vào menu “Giao nhiệm vụ”.",
        "(1) Nhập TIÊU ĐỀ, mô tả / yêu cầu.",
        "Chọn HẠN NỘP và (2) tích chọn các ĐƠN VỊ được giao.",
        "(3) Bấm “Giao nhiệm vụ”. Mỗi đơn vị xuất hiện một dòng ở bảng bên dưới với trạng thái “Chưa nộp”.",
    ])
    m.h(2, "12.2. Đơn vị nộp báo cáo tiến độ")
    m.figure("11b_nop_bao_cao", "Cán bộ đơn vị nộp báo cáo tiến độ nhiệm vụ")
    m.steps([
        "Mở nhiệm vụ, ở khối đơn vị mình chọn thẻ “Của tôi” rồi bấm “Xem”.",
        "Nhập NỘI DUNG BÁO CÁO vào ô soạn, bấm “Đính kèm minh chứng” để gửi kèm tệp nếu có, rồi bấm “Nộp báo cáo”. "
        "Trạng thái chuyển “Chờ duyệt”; bảng “Tiến độ duyệt” cập nhật ngay.",
        "Nếu bị “Trả lại”, xem ghi chú của chỉ huy, sửa và nộp lại (lịch sử các lần nộp được giữ lại).",
    ])
    m.h(2, "12.3. Chỉ huy duyệt báo cáo")
    m.figure("11c_duyet_bao_cao", "Nhiệm vụ đã được duyệt xong — chuyển trạng thái “Hoàn thành”")
    m.steps([
        "Ở dòng đơn vị đang “Chờ duyệt”, bấm “Duyệt”.",
        "Chọn “Đã duyệt” hoặc “Trả lại”, nhập ghi chú (bắt buộc nêu lý do khi trả lại), bấm “Xác nhận”.",
        "Khi TẤT CẢ đơn vị đều “Đã duyệt”, nhiệm vụ tự chuyển “Hoàn thành” (thanh tiến độ đầy, xuất hiện nút “Huỷ nhiệm vụ”). "
        "Quá hạn mà chưa xong sẽ hiển thị “Quá hạn”.",
    ])
    m.pagebreak()

    # ================================================================= 13
    m.h(1, "13. KÊNH CHỈ HUY (MẬT)")
    m.h(2, "13.1. Điều kiện truy cập")
    m.p("Chỉ vào được nếu bạn là Chỉ huy/Quản trị HOẶC được cấp “Quyền xem MẬT”. "
        "Người không đủ quyền bấm vào sẽ bị chặn (báo 403). Toàn bộ nội dung ở đây là MẬT — "
        "nghiêm cấm sao chụp, chuyển tiếp ra ngoài phạm vi được phép.")
    m.figure("19_kenh_bi_chan", "Tài khoản không có “Quyền xem MẬT” mở Kênh chỉ huy — bị chặn 403")
    m.h(2, "13.2. Họp bàn Ban Chỉ huy & Cấp uỷ")
    m.figure("12a_kenh_chi_huy_hop_ban", "Kênh chỉ huy – thẻ “Họp bàn BCH & Cấp uỷ”")
    m.steps([
        "Vào menu “Kênh chỉ huy (MẬT)”. Trang có 2 thẻ: (1) “Họp bàn BCH & Cấp uỷ” và (2) “Sổ công văn mật”.",
        "Ở thẻ (1): bấm một luồng bên trái để xem, hoặc tạo luồng mới bằng ô tiêu đề + “Tạo luồng”.",
        "(3) Gõ nội dung, đính kèm tệp nếu cần, bấm “Gửi”. Chỉ huy có thể “Đóng luồng”.",
    ])
    m.h(2, "13.3. Sổ công văn mật và ký nhận tiếp thu")
    m.figure("12b_so_cong_van", "Kênh chỉ huy – thẻ “Sổ công văn mật”")
    m.steps([
        "Chuyển sang thẻ “Sổ công văn mật”.",
        "(1) Chỉ huy vào sổ: chọn CHIỀU (Văn bản đi / Văn bản đến), nhập SỐ / KÝ HIỆU, chọn TRẠNG THÁI.",
        "(2) Nhập TRÍCH YẾU, cơ quan ban hành / nơi nhận, ngày tháng.",
        "(3) Bấm “Chọn tệp” (.pdf/.docx…) rồi “Vào sổ”. Số hiệu không được trùng theo từng chiều.",
        "Mọi thành viên đủ quyền: mở công văn, bấm (4) “Ký nhận đã tiếp thu” và có thể ghi “Phản hồi thực hiện”. "
        "Bấm “Tải tệp công văn” để xem file gốc.",
        "Chỉ huy theo dõi bảng ai đã / chưa ký nhận.",
    ])
    m.pagebreak()

    # ================================================================= 14
    m.h(1, "14. QUẢN LÝ NGƯỜI DÙNG (Quản trị / Chỉ huy)")
    m.figure("14_quan_ly_nguoi_dung", "Màn hình Quản lý người dùng")
    m.h(2, "14.1. Duyệt tài khoản đang chờ")
    m.p("Khu “Tài khoản chờ duyệt” ở đầu trang liệt kê người mới đăng ký. Bấm “Kích hoạt” để cho phép đăng nhập.")
    m.h(2, "14.2. Tạo tài khoản mới trực tiếp")
    m.steps([
        "Điền TÊN ĐĂNG NHẬP (chữ thường, số, dấu chấm/gạch), MẬT KHẨU tạm (≥ 8 ký tự có cả chữ và số), HỌ TÊN.",
        "(1) Chọn VAI TRÒ. Chỉ tài khoản admin mới tạo được tài khoản “Quản trị”.",
        "Chọn ĐƠN VỊ cho tài khoản (nếu có).",
        "(2) (admin) Tích “Cấp quyền vào Kênh Chỉ đạo – Báo cáo” nếu người này cần dùng kênh đó.",
        "(3) Bấm “Tạo tài khoản”. Tài khoản mới sẽ bị buộc đổi mật khẩu ở lần đăng nhập đầu.",
    ])
    m.h(2, "14.3. Phân quyền cho tài khoản đã có")
    m.p("Trong bảng danh sách, thao tác ngay trên từng dòng:")
    m.table(
        ["Cột / nút", "Tác dụng"],
        [["Vai trò (ô chọn)", "Đổi vai trò: Chiến sĩ ↔ Cán bộ ↔ Chỉ huy (↔ Quản trị nếu bạn là admin)"],
         ["Đơn vị (ô chọn)", "Gán / bỏ đơn vị cho tài khoản"],
         ["Xem MẬT (ô tích)", "Cấp / thu “Quyền xem MẬT” — cũng là điều kiện vào Kênh chỉ huy (MẬT)"],
         ["Kênh Chỉ đạo (ô tích)", "Bật / tắt quyền vào Kênh Chỉ đạo – Báo cáo (chỉ admin)"],
         ["Kích hoạt / Khoá", "Cho phép hoặc chặn tài khoản đăng nhập"],
         ["Cấp lại MK", "Đặt mật khẩu mới; người đó phải đổi lại ở lần đăng nhập kế tiếp"]],
        widths=[1.8, 4.8],
    )
    m.h(2, "14.4. Quy tắc an toàn (hệ thống tự chặn)")
    m.bullets([
        "Không thể tự hạ vai trò hoặc tự khoá chính tài khoản mình đang dùng.",
        "Luôn phải còn ít nhất MỘT tài khoản Chỉ huy/Quản trị đang hoạt động — không khoá/hạ quyền người cuối cùng.",
        "Tài khoản hệ thống (admin) không thể bị khoá, hạ quyền hay xoá.",
        "Chiến sĩ/Cán bộ không có “Quyền xem MẬT” sẽ bị chặn (403) khi cố mở Kênh chỉ huy (MẬT).",
    ])
    m.pagebreak()

    # ================================================================= 16
    m.h(1, "15. QUẢN LÝ ĐƠN VỊ (Quản trị)")
    m.p("Phần mềm đã nạp sẵn cơ cấu tổ chức chuẩn của Lữ đoàn (bảng dưới). Việc chính của bạn là "
        "vào “Quản lý người dùng” để gán từng tài khoản vào đúng đơn vị; chỉ thêm/sửa đơn vị khi tổ chức thay đổi.")
    m.table(
        ["Đơn vị (đầu mối)", "Loại", "Vai trò trong hệ thống"],
        [["Ban chỉ huy Lữ đoàn", "BCH Lữ đoàn", "Thấy mọi kênh; giao nhiệm vụ, duyệt báo cáo"],
         ["Cấp uỷ – Đảng bộ Lữ đoàn", "Cấp uỷ / Đảng bộ", "Tham gia Kênh chỉ huy (MẬT)"],
         ["Phòng Tham mưu", "Phòng / Ban", "Đầu mối tham mưu tác chiến, huấn luyện, SSCĐ"],
         ["Phòng Chính trị", "Phòng / Ban", "Đầu mối công tác đảng, công tác chính trị, tuyên huấn"],
         ["Phòng Hậu cần – Kỹ thuật", "Phòng / Ban", "Đầu mối bảo đảm hậu cần, kỹ thuật, quân y"],
         ["Tiểu đoàn 1 / Tiểu đoàn 2", "Tiểu đoàn", "Đầu mối nhận nhiệm vụ và báo cáo tiến độ"],
         ["Đại đội 5", "Đại đội", "Đầu mối đại đội trực thuộc"],
         ["Trạm bảo đảm", "Trạm", "Trạm bảo đảm thông tin"],
         ["Trung tâm 2", "Phòng / Ban", "Đầu mối trực thuộc"]],
        widths=[2.2, 1.5, 2.9],
    )
    m.figure("15_quan_ly_don_vi", "Màn hình Quản lý đơn vị")
    m.steps([
        "Vào menu “Quản lý đơn vị”.",
        "(1) Nhập TÊN ĐƠN VỊ và chọn LOẠI (Phòng/Ban, Tiểu đoàn, Đại đội, Trạm, BCH Lữ đoàn, Cấp uỷ/Đảng bộ).",
        "(2) Bấm “Thêm đơn vị”.",
        "Trong bảng: đổi loại, bật/tắt “Hoạt động”, hoặc “Xoá”.",
    ])
    m.note("Không xoá được đơn vị khi vẫn còn tài khoản trực thuộc — hãy chuyển các tài khoản sang đơn vị khác trước.")
    m.h(2, "15.1. Cấp quyền cho một bộ phận nhận & triển khai nhiệm vụ")
    m.steps([
        "Vào “Quản lý người dùng”, tạo tài khoản cho cán bộ của bộ phận (Phòng Tham mưu, Tiểu đoàn 2…).",
        "Gán tài khoản vào ĐÚNG đơn vị đó.",
        "Tích ô “Kênh Chỉ đạo” cho tài khoản (chỉ admin làm được).",
        "Từ đó: khi Ban chỉ huy giao nhiệm vụ cho đơn vị, cán bộ của đơn vị sẽ thấy nhiệm vụ và nộp báo cáo được (xem Mục 12); "
        "và trao đổi 2 chiều với Ban chỉ huy qua Kênh Chỉ đạo – Báo cáo (Mục 11).",
    ])
    m.pagebreak()

    # ================================================================= 17
    m.h(1, "16. HỒ SƠ CÁ NHÂN")
    m.figure("16_ho_so", "Màn hình Hồ sơ cá nhân")
    m.steps([
        "Vào menu “Hồ sơ cá nhân”.",
        "(1) Sửa HỌ TÊN rồi bấm “Lưu thay đổi”.",
        "(2) Đổi mật khẩu: nhập mật khẩu hiện tại, mật khẩu mới (≥ 8 ký tự có cả chữ và số), bấm “Đổi mật khẩu”.",
    ])
    m.pagebreak()

    # ================================================================= 18
    m.h(1, "17. TÀI KHOẢN “CÁ NHÂN” VÀ “NGƯỜI DÙNG” NHÌN THẤY GÌ")
    m.p("Menu hiển thị theo quyền. Hai ví dụ dưới đây giúp bạn đối chiếu.")
    m.figure("17_menu_can_bo", "Thanh menu của tài khoản “Cá nhân” (cán bộ được cấp Kênh Chỉ đạo)")
    m.figure("18_menu_chien_si", "Thanh menu của tài khoản “Người dùng” (chỉ xem)")
    m.bullets([
        "Không thấy một mục = bạn chưa được cấp quyền cho mục đó. Liên hệ quản trị nếu công việc yêu cầu.",
        "Thấy mục nhưng bấm vào bị báo “không đủ quyền” (403) = mục đó cần quyền cao hơn (ví dụ Kênh chỉ huy cần “Quyền xem MẬT”).",
    ])
    m.pagebreak()

    # ================================================================= 19
    m.h(1, "18. XỬ LÝ SỰ CỐ KHI SỬ DỤNG")
    m.p("Bảng dưới đây là các tình huống người dùng TỰ xử lý được. Sự cố về cài đặt, máy chủ, "
        "cơ sở dữ liệu, giao diện trắng trang… thuộc phần kỹ thuật — xem Mục 3.11 và báo trợ lý CNTT của đơn vị.")
    m.table(
        ["Hiện tượng", "Nguyên nhân thường gặp", "Cách xử lý"],
        [["Đăng nhập báo “Invalid username or password”", "Sai tên đăng nhập hoặc mật khẩu", "Gõ lại, chú ý chữ hoa/thường và phím CapsLock. Vẫn lỗi → nhờ quản trị cấp lại mật khẩu."],
         ["Báo “Tài khoản chưa được kích hoạt”", "Mới đăng ký, chưa được duyệt", "Liên hệ chỉ huy/quản trị để “Kích hoạt”."],
         ["Đăng nhập xong bị đưa tới màn hình đổi mật khẩu", "Tài khoản mới cấp / vừa được cấp lại mật khẩu", "Đổi mật khẩu theo Mục 4.2 rồi mới dùng tiếp."],
         ["Bị đẩy ra trang đăng nhập giữa chừng", "Phiên đăng nhập hết hạn", "Đăng nhập lại."],
         ["Bấm chức năng báo “Not enough permissions” (403)", "Vai trò/quyền chưa đủ", "Liên hệ quản trị để nâng vai trò, cấp “Quyền xem MẬT” hoặc bật cờ “Kênh Chỉ đạo”."],
         ["Không thấy mục cần dùng trên menu", "Chưa được cấp quyền", "Như trên."],
         ["Mở một mục báo “không tìm thấy” (404)", "Nội dung không tồn tại hoặc ngoài phạm vi bạn được xem", "Kiểm tra lại; nếu là nhiệm vụ/luồng của đơn vị khác thì bạn không xem được."],
         ["Không tạo được nội dung “MẬT”", "Không có “Quyền xem MẬT”", "Nhờ chỉ huy/quản trị cấp quyền."],
         ["Tải tệp lên báo lỗi định dạng / quá dung lượng", "Sai loại tệp hoặc file quá lớn", "Dùng đúng .pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx (hoặc ảnh với tin nhắn) và nén nhỏ lại."],
         ["Vào sổ công văn báo trùng số hiệu (409)", "Đã có công văn cùng chiều và cùng số", "Kiểm tra sổ; sửa số hiệu hoặc mở bản ghi đã có."],
         ["Gửi tin trong luồng báo lỗi (409)", "Luồng đã bị đóng", "Nhờ chỉ huy mở lại luồng."],
         ["Tạo tài khoản báo “tên đăng nhập đã tồn tại” (409)", "Trùng tên với tài khoản khác", "Đặt tên đăng nhập khác (thêm tên đơn vị, vd canbo.td1.b)."],
         ["Đổi mật khẩu báo mật khẩu mới chưa đạt (400)", "Chưa đủ mạnh", "Mật khẩu mới ≥ 8 ký tự, có CẢ chữ và số."],
         ["Đổi mật khẩu báo sai mật khẩu hiện tại (400)", "Gõ nhầm mật khẩu cũ", "Nhập lại đúng mật khẩu đang dùng; quên thì nhờ quản trị “Cấp lại mật khẩu”."],
         ["Gõ tìm kiếm tiếng Việt không ra kết quả", "Khác dấu / khác cách bỏ dấu", "Gõ đúng dấu, hoặc thử gõ không dấu / ít từ khoá hơn."],
         ["Danh sách trống trơn dù chắc chắn có dữ liệu", "Bộ lọc đang bật (khoảng ngày, trạng thái, đơn vị)", "Xoá / đặt lại các ô lọc trên đầu danh sách rồi xem lại."],
         ["Nhập danh bạ từ Excel không lên dữ liệu", "File không đúng .xlsx/.csv, hoặc dòng tiêu đề cột nằm sai vị trí", "Lưu lại đúng định dạng .xlsx/.csv, để dòng tiêu đề ở hàng đầu; thử lại."],
         ["Ảnh / tệp đính kèm bấm vào báo “không tìm thấy” (404)", "Tệp đã bị xoá, hoặc lỗi phía máy chủ tệp", "Báo người đăng tải lại; nếu nhiều tệp cùng lỗi → báo trợ lý CNTT (Mục 3.11)."],
         ["Vừa đăng nhập đã bị đăng xuất, lặp lại nhiều lần", "Giờ máy trạm lệch nhiều so với máy chủ", "Chỉnh lại ngày giờ máy đang dùng cho đúng; vẫn lỗi → báo trợ lý CNTT."],
         ["Trang giao diện trắng / báo không kết nối được máy chủ", "Máy chủ chưa chạy hoặc địa chỉ giao diện cấu hình sai", "Thử lại sau ít phút; nếu cả đơn vị cùng bị → báo trợ lý CNTT (Mục 3.11)."]],
        widths=[2.2, 2.0, 2.4],
    )
    m.pagebreak()

    # ================================================================= 20
    m.h(1, "19. PHỤ LỤC A — BẢNG PHÂN QUYỀN")
    m.table(
        ["Chức năng", "Chiến sĩ", "Cán bộ", "Chỉ huy", "Quản trị"],
        [["Xem tin tức / GDCT / thông báo / chỉ thị", "Có", "Có", "Có", "Có"],
         ["Đăng & sửa Tin tức, Giáo dục chính trị", "—", "Có", "Có", "Có"],
         ["Duyệt / trả lại bài Tin tức", "—", "—", "Có", "Có"],
         ["Ban hành Chỉ thị – Nhiệm vụ", "—", "—", "Có", "Có"],
         ["Kênh Chỉ đạo – Báo cáo (luồng, giao nhiệm vụ)", "Khi được bật cờ", "Khi được bật cờ", "Có", "Có"],
         ["Duyệt báo cáo / giao – huỷ nhiệm vụ", "—", "—", "Có", "Có"],
         ["Kênh chỉ huy (MẬT): họp bàn, công văn", "Khi có Quyền xem MẬT", "Khi có Quyền xem MẬT", "Có", "Có"],
         ["Vào sổ / sửa công văn, ghi biên bản, điểm danh người khác", "—", "—", "Có", "Có"],
         ["Quản lý người dùng (kích hoạt, phân quyền)", "—", "—", "Có", "Có"],
         ["Tạo tài khoản “Quản trị”, Quản lý đơn vị", "—", "—", "—", "Có"]],
        widths=[3.0, 1.0, 1.0, 0.8, 0.9],
    )
    m.p("Ghi chú: “Khi được bật cờ” = quản trị tích ô “Kênh Chỉ đạo” cho tài khoản. "
        "“Khi có Quyền xem MẬT” = quản trị tích ô “Xem MẬT” cho tài khoản.")
    m.pagebreak()

    # ================================================================= 21
    m.h(1, "20. PHỤ LỤC B — CÁC TRẠNG THÁI THƯỜNG GẶP")
    m.h(2, "Bài viết Tin tức")
    m.table(["Trạng thái", "Ý nghĩa"],
            [["Chờ duyệt", "Cán bộ vừa đăng/sửa, chưa hiển thị công khai"],
             ["Đã duyệt", "Đã được chỉ huy duyệt, hiển thị theo bậc phân loại"],
             ["Trả lại", "Chỉ huy trả về cho tác giả sửa"]], widths=[1.6, 5.0])
    m.h(2, "Chỉ thị – Nhiệm vụ")
    m.table(["Trạng thái", "Ý nghĩa"],
            [["Bản nháp", "Chỉ chỉ huy thấy"], ["Đã ban hành", "Mọi tài khoản thấy, có thể bấm “Tôi đã tiếp thu”"]],
            widths=[1.6, 5.0])
    m.h(2, "Giao nhiệm vụ (theo từng đơn vị)")
    m.table(["Trạng thái", "Ý nghĩa"],
            [["Chưa nộp", "Đơn vị chưa gửi báo cáo"], ["Chờ duyệt", "Đơn vị đã nộp, chờ chỉ huy xem"],
             ["Đã duyệt", "Chỉ huy chấp nhận báo cáo"], ["Trả lại", "Chỉ huy yêu cầu bổ sung / làm lại"]],
            widths=[1.6, 5.0])
    m.h(2, "Nhiệm vụ (tổng thể)")
    m.table(["Trạng thái", "Ý nghĩa"],
            [["Chưa giao", "Chưa gán đơn vị nào"], ["Đang thực hiện", "Đã giao, còn đơn vị chưa được duyệt"],
             ["Hoàn thành", "Tất cả đơn vị đã duyệt"], ["Quá hạn", "Quá ngày hạn mà chưa hoàn thành"]],
            widths=[1.6, 5.0])
    m.h(2, "Công văn")
    m.table(["Trạng thái", "Ý nghĩa"],
            [["Mới", "Vừa vào sổ"], ["Đang xử lý", "Đang được giải quyết"],
             ["Đã xử lý", "Đã giải quyết xong"], ["Lưu trữ", "Đưa vào lưu"]], widths=[1.6, 5.0])

    d.add_paragraph()
    end = d.add_paragraph("— HẾT —")
    end.alignment = WD_ALIGN_PARAGRAPH.CENTER
    end.runs[0].bold = True

    import time

    candidates = [OUT] + [OUT.with_name(f"HUONG_DAN_SU_DUNG_moi{i}.docx") for i in ("", "2", "3", "4", "5")]
    saved = None
    for cand in candidates:
        try:
            m.d.save(str(cand))
            saved = cand
            break
        except PermissionError:
            continue
    if saved is None:
        saved = OUT.with_name(f"HUONG_DAN_SU_DUNG_{int(time.time())}.docx")
        m.d.save(str(saved))
    if saved == OUT:
        print("Đã tạo:", OUT)
    else:
        print("!!", OUT.name, "đang MỞ trong Word nên không ghi đè được.")
        print("   Đã lưu bản mới vào:", saved.name)
        print("   -> Đóng tất cả file .docx đang mở trong Word, xoá các bản cũ,")
        print("      rồi đổi tên bản mới thành HUONG_DAN_SU_DUNG.docx (hoặc chạy lại lệnh này).")
