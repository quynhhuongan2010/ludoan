"""Kiem thu co che luu tru bao mat (SECURE_UPLOAD_DIR) cho tep MAT.

Xac nhan:
1. File luu vao storage/secure_uploads/, KHONG luu vao storage/uploads/ (khong bi lo qua /static).
2. Chi user co quyen xem MAT moi goi duoc get_download_target thanh cong.
3. User thieu quyen bi chan 403.
4. Co che fallback tuong thich nguoc cho cac file cu truoc khi nang cap.
5. delete_secure_upload don sach file vat ly.
"""

import io
import os
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.security import hash_password
from app.core.uploads import (
    DOCUMENT_EXTENSIONS,
    delete_secure_upload,
    save_secure_upload,
)
from app.models.command_thread import CommandMessage, CommandThread
from app.models.official_dispatch import OfficialDispatch
from app.models.user import User
from app.schemas.official_dispatch import DispatchUpdate
from app.services import command_thread_service, official_dispatch_service

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

fails = []


def check(label: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  [PASS] {label}")
    else:
        print(f"  [FAIL] {label} -> {detail}")
        fails.append(label)


def run_tests():
    print("=== BAT DAU KIEM THU CO CHE LUU TRU TEP MAT ===")

    # 1. Setup users
    cmd = User(
        username="commander",
        hashed_password=hash_password("123456"),
        full_name="Lữ trưởng",
        role=1,
        is_active=True,
        clearance=False,
    )
    cleared_user = User(
        username="cleared_user",
        hashed_password=hash_password("123456"),
        full_name="Cán bộ cơ mật",
        role=5,
        is_active=True,
        clearance=True,
    )
    soldier = User(
        username="soldier",
        hashed_password=hash_password("123456"),
        full_name="Chiến sĩ thông thường",
        role=5,
        is_active=True,
        clearance=False,
    )
    db.add_all([cmd, cleared_user, soldier])
    db.commit()
    db.refresh(cmd)
    db.refresh(cleared_user)
    db.refresh(soldier)

    # 2. Test save_secure_upload
    sample_content = b"%PDF-1.4 Test Mat Lu Doan 21"
    upload_file = UploadFile(
        file=io.BytesIO(sample_content),
        filename="ke_hoach_tac_chien.pdf",
        headers={"content-type": "application/pdf"},
    )
    saved = save_secure_upload(
        upload_file, subdir="dispatches", allowed_ext=DOCUMENT_EXTENSIONS
    )

    check(
        "URL khong bat dau bang /static/",
        not saved.url.startswith("/static/"),
        f"got {saved.url}",
    )
    check("URL co tien to /secure/", saved.url.startswith("/secure/dispatches/"))

    file_on_disk = settings.secure_upload_path / "dispatches" / saved.stored_name
    check("File da duoc ghi vao secure_upload_path", file_on_disk.is_file())

    file_in_static = settings.upload_path / "dispatches" / saved.stored_name
    check("File TUYET DOI KHONG nam trong upload_path (/static/)", not file_in_static.exists())

    # 3. Test OfficialDispatch voi secure upload
    dispatch_payload = DispatchUpdate(
        direction="den",
        doc_type="chi_thi",
        dispatch_number="12/CT-BTL",
        summary="Chỉ thị sẵn sàng chiến đấu",
        security_level="mat",
    )
    dispatch_detail = official_dispatch_service.create_dispatch(
        db, cmd, dispatch_payload, saved
    )
    check("Tao cong van mat thanh cong", dispatch_detail.id is not None)
    check(
        "attachment_url cong van luu secure path",
        dispatch_detail.attachment_url.startswith("/secure/dispatches/"),
    )

    # 4. Test download target quyen MAT
    # 4a. Commander tai duoc
    path, fname, ctype = official_dispatch_service.get_download_target(
        db, cmd, dispatch_detail.id
    )
    check("Commander lay duoc download target", path.is_file() and fname == "ke_hoach_tac_chien.pdf")

    # 4b. Cleared user (co cờ clearance) tai duoc
    path2, fname2, _ = official_dispatch_service.get_download_target(
        db, cleared_user, dispatch_detail.id
    )
    check("Cleared user lay duoc download target", path2.is_file() and fname2 == "ke_hoach_tac_chien.pdf")

    # 4c. Soldier (khong co co clearance, khong phai commander) bi chan 403
    blocked = False
    try:
        official_dispatch_service.get_download_target(db, soldier, dispatch_detail.id)
    except HTTPException as e:
        blocked = e.status_code == 403
    check("Soldier bi chan 403 khi tai cong van mat", blocked)

    # 5. Test fallback tuong thich nguoc cho file cu trong upload_path (/static/command/...)
    old_file_name = "old_secret_file.pdf"
    old_target_dir = settings.upload_path / "command"
    old_target_dir.mkdir(parents=True, exist_ok=True)
    old_file_path = old_target_dir / old_file_name
    old_file_path.write_bytes(b"Old secret dispatch content")

    old_dispatch = OfficialDispatch(
        direction="di",
        doc_type="cong_van",
        dispatch_number="99/CV-LD",
        summary="Cong van cu tu phien ban truoc",
        security_level="mat",
        attachment_url=f"/static/command/{old_file_name}",
        attachment_name="old_secret_file.pdf",
        created_by_id=cmd.id,
    )
    db.add(old_dispatch)
    db.commit()
    db.refresh(old_dispatch)

    old_path, old_fname, _ = official_dispatch_service.get_download_target(
        db, cmd, old_dispatch.id
    )
    check(
        "Fallback doc thanh cong file cu trong static/command",
        old_path.is_file() and old_fname == "old_secret_file.pdf",
    )

    # 6. Test delete_secure_upload
    delete_secure_upload(saved.url)
    check("delete_secure_upload da xoa file secure tren o dia", not file_on_disk.exists())

    delete_secure_upload(f"/static/command/{old_file_name}")
    check("delete_secure_upload da xoa ca file fallback cu", not old_file_path.exists())

    # 7. Test CommandThread Document & Message Attachment
    thread = CommandThread(
        title="Hop mat Ban Chi huy",
        classification="mat",
        created_by_id=cmd.id,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    # 7a. Upload document vao thread
    doc_upload = UploadFile(
        file=io.BytesIO(b"PK\x03\x04\x14\x00\x06\x00Tai lieu mat BCH"),
        filename="bien_ban_hop.docx",
        headers={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    )
    doc_saved = save_secure_upload(doc_upload, subdir="command_docs", allowed_ext=DOCUMENT_EXTENSIONS)
    doc_out = command_thread_service.upload_document(
        db, cmd, thread.id, "Tài liệu mật BCH", "chung", doc_saved
    )
    check("Upload document luong mat thanh cong", doc_out.id is not None)
    check("Document URL bat dau bang /secure/", doc_out.file_url.startswith("/secure/command_docs/"))

    # Commander tai duoc doc
    doc_path, _, _ = command_thread_service.get_download_target(db, cmd, thread.id, doc_out.id)
    check("Commander tai duoc document trong luong mat", doc_path.is_file())

    # Soldier bi chan
    blocked_doc = False
    try:
        command_thread_service.get_download_target(db, soldier, thread.id, doc_out.id)
    except HTTPException as e:
        blocked_doc = e.status_code in (403, 404)
    check("Soldier bi chan khi tai document trong luong mat", blocked_doc)

    # 7b. Message attachment
    msg_upload = UploadFile(
        file=io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + (b"\x00" * 20)),
        filename="so_do.png",
        headers={"content-type": "image/png"},
    )
    msg_saved = save_secure_upload(msg_upload, subdir="command_messages", allowed_ext={".png", ".jpg"})
    msg_out = command_thread_service.post_message(
        db, cmd, thread.id, "Gửi các đồng chí sơ đồ", msg_saved
    )
    check("Post message kem attachment mat thanh cong", msg_out.attachment_url.startswith("/secure/command_messages/"))

    # Download message attachment
    msg_path, _, _ = command_thread_service.get_message_attachment_download_target(
        db, cmd, thread.id, msg_out.id
    )
    check("Tai message attachment thanh cong qua endpoint", msg_path.is_file())

    # Don dep doc va msg attachment
    delete_secure_upload(doc_saved.url)
    delete_secure_upload(msg_saved.url)

    print("\n=== KET QUA KIEM THU ===")
    if fails:
        print(f"CO {len(fails)} TEST THAT BAI: {fails}")
        sys.exit(1)
    else:
        print("TAT CA TEST DEU PASS 100%!")


if __name__ == "__main__":
    run_tests()
