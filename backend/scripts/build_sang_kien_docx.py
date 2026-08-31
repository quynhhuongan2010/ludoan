# -*- coding: utf-8 -*-
"""Xuất BÁO CÁO THUYẾT MINH SÁNG KIẾN từ Markdown sang Word (.docx).

Đọc:  BAO_CAO_THUYET_MINH_SANG_KIEN.md  (thư mục gốc dự án)
Ghi:  BAO_CAO_THUYET_MINH_SANG_KIEN.docx (cùng thư mục)

Chạy:
    backend/venv/Scripts/python.exe scripts/build_sang_kien_docx.py

Bộ chuyển đổi Markdown tối giản, đủ dùng cho bố cục của báo cáo:
tiêu đề (#, ##, ###), đoạn văn, danh sách (-, 1.), bảng (|...|),
khối mã (```), trích dẫn (>), in đậm **...** và mã `...` trong dòng.
"""

import pathlib
import re
import sys

try:  # bảo đảm in được tiếng Việt trên console Windows (cp1252)
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "BAO_CAO_THUYET_MINH_SANG_KIEN.md"
OUT = ROOT / "BAO_CAO_THUYET_MINH_SANG_KIEN.docx"

FONT = "Times New Roman"
GREEN = RGBColor(0x1F, 0x4C, 0x30)
INK = RGBColor(0x22, 0x22, 0x22)

INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")


def _set_base_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(13)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.3


def _add_runs(paragraph, text: str) -> None:
    """Ghi text vào paragraph, xử lý **đậm** và `mã`."""
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
    # rows[1] là dòng ngăn cách '---' của Markdown -> bỏ
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

        # --- khối mã ```
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

        # --- bảng
        if line.startswith("|") and line.endswith("|"):
            cells = [_clean_cell(c) for c in line.strip("|").split("|")]
            table_buf.append(cells)
            continue
        elif table_buf:
            _flush_table(doc, table_buf)
            table_buf = []

        # --- ngăn cách / trống
        if not line.strip():
            continue
        if line.strip() == "---":
            continue

        # --- tiêu đề
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

        # --- trích dẫn
        if line.startswith(">"):
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Pt(18)
            run = para.add_run(line.lstrip("> ").strip())
            run.italic = True
            run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            continue

        # --- danh sách
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

        # --- đoạn văn thường
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
