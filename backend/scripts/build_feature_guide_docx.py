# -*- coding: utf-8 -*-
"""Xuất HƯỚNG DẪN KHAI THÁC TÍNH NĂNG (kèm ảnh minh hoạ thật) tu Markdown sang
Word (.docx). Giong `build_sang_kien_docx.py` nhung co them ho tro nhung anh
(`![alt](duong/dan/anh.png)`) - dung rieng cho tai lieu nay de khong dung cham
toi script bao cao sang kien da duyet.

Doc:  HUONG_DAN_KHAI_THAC_TINH_NANG.md   (thu muc goc du an)
Anh:  docs/screenshots_khai_thac/*.png    (sinh boi scripts/capture_feature_screenshots.py)
Ghi:  HUONG_DAN_KHAI_THAC_TINH_NANG.docx (cung thu muc)

Chay:
    backend/venv/Scripts/python.exe scripts/build_feature_guide_docx.py
"""

import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "HUONG_DAN_KHAI_THAC_TINH_NANG.md"
OUT = ROOT / "HUONG_DAN_KHAI_THAC_TINH_NANG.docx"

FONT = "Times New Roman"
GREEN = RGBColor(0x1F, 0x4C, 0x30)
INK = RGBColor(0x22, 0x22, 0x22)

INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")
IMAGE = re.compile(r"^!\[(.*?)\]\((.*?)\)$")


def _set_base_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(13)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.3


def _add_runs(paragraph, text: str) -> None:
    for chunk in INLINE.split(text):
        if not chunk:
            continue
        if chunk.startswith("**") and chunk.endswith("**"):
            run = paragraph.add_run(chunk[2:-2])
            run.bold = True
        elif chunk.startswith("`") and chunk.endswith("`"):
            run = paragraph.add_run(chunk[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(11)
        else:
            paragraph.add_run(chunk)


def _clean_cell(text: str) -> str:
    return text.replace("\\|", "|").strip()


def _flush_table(doc: Document, rows: list[list[str]]) -> None:
    if not rows:
        return
    header, body = rows[0], rows[2:]
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, cell_text in enumerate(header):
        cell = table.rows[0].cells[i]
        cell.paragraphs[0].text = ""
        _add_runs(cell.paragraphs[0], cell_text)
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for row in body:
        cells = table.add_row().cells
        for i in range(len(header)):
            value = row[i] if i < len(row) else ""
            cells[i].paragraphs[0].text = ""
            _add_runs(cells[i].paragraphs[0], value)
    doc.add_paragraph()


def _flush_code(doc: Document, lines: list[str]) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Pt(12)
    run = para.add_run("\n".join(lines))
    run.font.name = "Consolas"
    run.font.size = Pt(10.5)
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)


def _add_image(doc: Document, alt: str, rel_path: str) -> None:
    img_path = (ROOT / rel_path).resolve()
    if not img_path.is_file():
        para = doc.add_paragraph()
        run = para.add_run(f"[Không tìm thấy ảnh: {rel_path}]")
        run.italic = True
        run.font.color.rgb = RGBColor(0xAA, 0x22, 0x22)
        return
    doc.add_picture(str(img_path), width=Inches(6.3))
    last = doc.paragraphs[-1]
    last.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if alt:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(alt)
        run.italic = True
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    doc.add_paragraph()


def build() -> None:
    if not SRC.exists():
        raise SystemExit(f"Không tìm thấy {SRC}")

    md = SRC.read_text(encoding="utf-8").splitlines()
    doc = Document()
    _set_base_style(doc)

    table_buf: list[list[str]] = []
    code_buf: list[str] | None = None

    for raw in md:
        line = raw.rstrip()

        if line.strip().startswith("```"):
            if code_buf is None:
                code_buf = []
            else:
                _flush_code(doc, code_buf)
                code_buf = None
            continue
        if code_buf is not None:
            code_buf.append(raw)
            continue

        if line.startswith("|") and line.endswith("|"):
            cells = [_clean_cell(c) for c in line.strip("|").split("|")]
            table_buf.append(cells)
            continue
        elif table_buf:
            _flush_table(doc, table_buf)
            table_buf = []

        if not line.strip():
            continue
        if line.strip() == "---":
            continue

        m_img = IMAGE.match(line.strip())
        if m_img:
            _add_image(doc, m_img.group(1), m_img.group(2))
            continue

        if line.startswith("### "):
            h = doc.add_heading(level=3)
            _add_runs(h, line[4:])
            for run in h.runs:
                run.font.name = FONT
                run.font.color.rgb = GREEN
            continue
        if line.startswith("## "):
            h = doc.add_heading(level=2)
            _add_runs(h, line[3:])
            for run in h.runs:
                run.font.name = FONT
                run.font.color.rgb = GREEN
            continue
        if line.startswith("# "):
            h = doc.add_heading(level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _add_runs(h, line[2:])
            for run in h.runs:
                run.font.name = FONT
                run.font.color.rgb = GREEN
            continue

        if line.startswith(">"):
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Pt(18)
            run = para.add_run(line.lstrip("> ").strip())
            run.italic = True
            run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            continue

        m_ul = re.match(r"^(\s*)[-*]\s+(.*)$", raw)
        m_ol = re.match(r"^(\s*)\d+\.\s+(.*)$", raw)
        if m_ul:
            para = doc.add_paragraph(style="List Bullet")
            _add_runs(para, m_ul.group(2))
            continue
        if m_ol:
            para = doc.add_paragraph(style="List Number")
            _add_runs(para, m_ol.group(2))
            continue

        # dong "**Buoc N — ...:**" dung nhu tieu de nho -> can giua, dam
        if line.strip().startswith("**Bước") or line.strip().startswith("**Kết quả"):
            para = doc.add_paragraph()
            _add_runs(para, line)
            continue

        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        _add_runs(para, line)

    if table_buf:
        _flush_table(doc, table_buf)
    if code_buf:
        _flush_code(doc, code_buf)

    doc.save(OUT)
    print("Đã tạo:", OUT)


if __name__ == "__main__":
    build()
