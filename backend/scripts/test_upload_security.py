"""
Script kiem thu tu dong tinh nang Kiem soat an toan tep tai len (Step 4 - v7.4.0).
Kiem thu:
1. File hop le (PDF, PNG, JPEG, DOCX) co dung chu ky nhi phan -> Upload thanh cong.
2. File gia mao duoi tep (Extension Spoofing):
   - File co header EXE (MZ) doi duoi thanh .pdf hoac .png -> Bi chan ngay lap tuc.
   - File co header ELF doi duoi thanh .jpg -> Bi chan ngay lap tuc.
   - File co chua script doc hai doi duoi thanh anh/tai lieu -> Bi chan.
   - File van ban thuan doi duoi thanh .pdf / .docx -> Bi chan (khong dung chu ky).
3. Lam sach ten file chong Path Traversal (../../../etc/passwd -> passwd).
4. Chan file rong va file vuot qua gioi han dung luong MB.
"""

import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException, UploadFile
from app.core.uploads import (
    DOCUMENT_EXTENSIONS,
    IMAGE_EXTENSIONS,
    delete_secure_upload,
    delete_upload,
    sanitize_filename,
    save_secure_upload,
    save_upload,
)


def test_upload_security():
    print("=== BẮT ĐẦU KIỂM THỬ AN TOÀN TỆP TẢI LÊN (v7.4.0) ===")

    created_urls = []

    try:
        # 1. Kiem thu lam sach ten file (Path Traversal Sanitization)
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
        assert sanitize_filename("safe_document.pdf") == "safe_document.pdf"
        assert sanitize_filename("test\x00null\r\n.png") == "testnull.png"
        print("-> [PASS] Làm sạch tên tệp chống Path Traversal và Null-byte đạt chuẩn.")

        # 2. Upload file hop le
        # 2a. Valid PDF
        pdf_content = b"%PDF-1.5 Content of official order Lu Doan 21"
        pdf_file = UploadFile(
            file=io.BytesIO(pdf_content),
            filename="ke_hoach_chuan.pdf",
            headers={"content-type": "application/pdf"},
        )
        saved_pdf = save_upload(pdf_file, subdir="test_sec", allowed_ext=DOCUMENT_EXTENSIONS)
        created_urls.append(saved_pdf.url)
        assert saved_pdf.stored_name.endswith(".pdf")
        print("-> [PASS] Tệp PDF chuẩn (%PDF-) tải lên thành công.")

        # 2b. Valid PNG
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + (b"\x00" * 50)
        png_file = UploadFile(
            file=io.BytesIO(png_content),
            filename="anh_chup.png",
            headers={"content-type": "image/png"},
        )
        saved_png = save_upload(png_file, subdir="test_sec", allowed_ext=IMAGE_EXTENSIONS)
        created_urls.append(saved_png.url)
        assert saved_png.stored_name.endswith(".png")
        print("-> [PASS] Tệp PNG chuẩn (\x89PNG) tải lên thành công.")

        # 2c. Valid JPEG
        jpg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF" + (b"\x00" * 50)
        jpg_file = UploadFile(
            file=io.BytesIO(jpg_content),
            filename="anh_qd.jpg",
            headers={"content-type": "image/jpeg"},
        )
        saved_jpg = save_upload(jpg_file, subdir="test_sec", allowed_ext=IMAGE_EXTENSIONS)
        created_urls.append(saved_jpg.url)
        print("-> [PASS] Tệp JPEG chuẩn (SOI \xff\xd8\xff) tải lên thành công.")

        # 2d. Valid DOCX
        docx_content = b"PK\x03\x04\x14\x00\x06\x00" + (b"\x00" * 50)
        docx_file = UploadFile(
            file=io.BytesIO(docx_content),
            filename="bao_cao.docx",
            headers={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        )
        saved_docx = save_secure_upload(docx_file, subdir="test_sec", allowed_ext=DOCUMENT_EXTENSIONS)
        created_urls.append(saved_docx.url)
        print("-> [PASS] Tệp DOCX chuẩn (PK Zip Container) lưu bảo mật thành công.")

        # 3. Kiem thu chan tep gia mao va chua ma thuc thi doc hai
        # 3a. File EXE gia mao PDF (tao header MZ dong)
        exe_header = bytes([0x4D, 0x5A, 0x90, 0x00, 0x03, 0x00]) + b"Windows Binary Mock"
        fake_pdf = UploadFile(
            file=io.BytesIO(exe_header),
            filename="test_binary.pdf",
            headers={"content-type": "application/pdf"},
        )
        blocked_exe = False
        try:
            save_upload(fake_pdf, subdir="test_sec", allowed_ext=DOCUMENT_EXTENSIONS)
        except HTTPException as e:
            if e.status_code == 400 and "MZ/PE" in e.detail:
                blocked_exe = True
                print(f"-> [PASS] Chặn thành công tệp Windows EXE giả mạo PDF: {e.detail}")
        assert blocked_exe, "File Windows EXE giả mạo phải bị chặn 100%!"

        # 3b. File Linux ELF gia mao PNG (tao header ELF dong)
        elf_header = bytes([0x7F, 0x45, 0x4C, 0x46, 0x02, 0x01]) + b"Linux Binary Mock"
        fake_png = UploadFile(
            file=io.BytesIO(elf_header),
            filename="test_elf.png",
            headers={"content-type": "image/png"},
        )
        blocked_elf = False
        try:
            save_upload(fake_png, subdir="test_sec", allowed_ext=IMAGE_EXTENSIONS)
        except HTTPException as e:
            if e.status_code == 400 and "Linux (ELF)" in e.detail:
                blocked_elf = True
                print(f"-> [PASS] Chặn thành công tệp Linux ELF giả mạo PNG: {e.detail}")
        assert blocked_elf, "File Linux ELF giả mạo phải bị chặn 100%!"

        # 3c. Script gia mao JPG (tao payload dong)
        script_payload = b"<" + b"?php " + b"echo 'test';"
        fake_jpg_script = UploadFile(
            file=io.BytesIO(script_payload),
            filename="test_script.jpg",
            headers={"content-type": "image/jpeg"},
        )
        blocked_shell = False
        try:
            save_upload(fake_jpg_script, subdir="test_sec", allowed_ext=IMAGE_EXTENSIONS)
        except HTTPException as e:
            if e.status_code == 400 and ("mã script" in e.detail or "không hợp lệ" in e.detail):
                blocked_shell = True
                print(f"-> [PASS] Chặn thành công Script giả mạo JPG: {e.detail}")
        assert blocked_shell, "Script giả mạo phải bị chặn 100%!"

        # 3d. File van ban gia mao DOCX (khong dung chu ky PK\x03\x04)
        fake_docx = UploadFile(
            file=io.BytesIO(b"This is just plain text, not a docx file"),
            filename="fake.docx",
            headers={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        )
        blocked_docx = False
        try:
            save_secure_upload(fake_docx, subdir="test_sec", allowed_ext=DOCUMENT_EXTENSIONS)
        except HTTPException as e:
            if e.status_code == 400 and "không hợp lệ" in e.detail:
                blocked_docx = True
                print(f"-> [PASS] Chặn thành công tệp giả mạo chữ ký DOCX: {e.detail}")
        assert blocked_docx, "File giả mạo DOCX phải bị chặn!"

        # 4. Kiem thu file rong va file vuot dung luong
        empty_file = UploadFile(
            file=io.BytesIO(b""),
            filename="empty.pdf",
            headers={"content-type": "application/pdf"},
        )
        blocked_empty = False
        try:
            save_upload(empty_file, subdir="test_sec", allowed_ext=DOCUMENT_EXTENSIONS)
        except HTTPException as e:
            if e.status_code == 400 and "File rỗng" in e.detail:
                blocked_empty = True
        assert blocked_empty, "File rỗng phải bị chặn!"
        print("-> [PASS] Tệp rỗng (0 bytes) bị chặn chuẩn xác.")

        # File vuot qua max_mb (test voi limit 1MB)
        oversized_data = b"%PDF-" + (b"A" * (2 * 1024 * 1024))
        oversized_file = UploadFile(
            file=io.BytesIO(oversized_data),
            filename="big.pdf",
            headers={"content-type": "application/pdf"},
        )
        blocked_size = False
        try:
            save_upload(oversized_file, subdir="test_sec", allowed_ext=DOCUMENT_EXTENSIONS, max_mb=1)
        except HTTPException as e:
            if e.status_code == 400 and "vượt quá giới hạn" in e.detail:
                blocked_size = True
        assert blocked_size, "File vượt quá giới hạn phải bị chặn!"
        print("-> [PASS] Tệp vượt quá giới hạn dung lượng bị chặn chuẩn xác.")

        print("\n=== TẤT CẢ KIỂM THỬ AN TOÀN TỆP TẢI LÊN ĐÃ ĐẠT 100%! ===")

    finally:
        # Don dep cac file test
        for u in created_urls:
            if u.startswith("/secure/"):
                delete_secure_upload(u)
            else:
                delete_upload(u)


if __name__ == "__main__":
    test_upload_security()
