"""Kiem thu tinh nang chat nang cao (v8.1.0): tra loi / sua / thu hoi / reaction /
ghim / chuyen tiep / tin he thong / tim kiem / tat thong bao / luu tru / bien nhan.

SQLite in-memory, goi thang service (khong can uvicorn). Chay tu backend/:
    venv/Scripts/python.exe -m scripts.test_chat_features
"""

import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models  # noqa: F401  (dang ky toan bo mapper)
from app.models.chat import ChatMessage
from app.models.unit import Unit
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, GroupChatCreate
from app.services import chat_service as svc

_PASS = 0
_FAIL = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    ok = bool(cond)
    print(("PASS " if ok else "FAIL ") + label + (f"  -> {detail}" if detail else ""))
    if ok:
        _PASS += 1
    else:
        _FAIL += 1


def expect_http(label: str, code: int, fn, *args, **kwargs) -> None:
    try:
        fn(*args, **kwargs)
        check(label, False, f"khong raise (mong doi {code})")
    except HTTPException as e:
        check(label, e.status_code == code, f"HTTP {e.status_code}: {e.detail}")


def main() -> int:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    db.add_all([
        Unit(id=1, name="Ban chỉ huy Lữ đoàn", unit_kind="bch_lu_doan"),
        Unit(id=2, name="Tiểu đoàn 1", unit_kind="tieu_doan"),
    ])
    db.commit()

    def mk(uid, uname, role, unit=2):
        u = User(id=uid, username=uname, hashed_password="h", full_name=uname.upper(),
                 rank="Đại uý", position="Trợ lý", role=role, is_active=True, unit_id=unit)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u

    cmd = mk(1, "lu_truong", 1, unit=1)   # Ban chi huy -> tao nhom la da_duyet, is_command
    off1 = mk(2, "canbo_a", 4)
    off2 = mk(3, "canbo_b", 4)
    off3 = mk(4, "canbo_c", 4)
    outsider = mk(5, "canbo_d", 4)

    # ------------------------------------------------------------------ nhom + 1-1
    grp = svc.create_group_chat(
        db, cmd, GroupChatCreate(name="Kíp trực A", member_ids=[off1.id, off2.id, off3.id])
    )
    direct = svc.get_or_create_direct_chat(db, off1, off2.id)
    check("tao nhom (role chi huy) -> da_duyet", grp.status == "da_duyet")
    check("nhom co 4 thanh vien", len(grp.participants) == 4, str(len(grp.participants)))

    m1 = svc.send_message(db, off1, grp.id, ChatMessageCreate(content="Chào kíp trực, triển khai nhiệm vụ SSCĐ"))
    m2 = svc.send_message(db, off2, grp.id, ChatMessageCreate(content="Rõ, đã nhận"))

    # ------------------------------------------------------------------ 1. Tra loi / trich dan
    reply = svc.send_message(
        db, off3, grp.id, ChatMessageCreate(content="Bổ sung quân số", reply_to_id=m1.id)
    )
    check("reply: reply_to duoc dinh kem", reply.reply_to is not None and reply.reply_to.id == m1.id)
    expect_http("reply toi tin khong thuoc hoi thoai -> 404", 404,
                svc.send_message, db, off3, grp.id,
                ChatMessageCreate(content="x", reply_to_id=999999))

    # ------------------------------------------------------------------ 2. Sua tin
    edited = svc.edit_message(db, off1, grp.id, m1.id, "Chào kíp trực, TRIỂN KHAI ngay nhiệm vụ SSCĐ")
    check("sua tin (nguoi gui) -> is_edited", edited.is_edited and "TRIỂN KHAI ngay" in edited.content)
    expect_http("sua tin nguoi khac -> 403", 403,
                svc.edit_message, db, off2, grp.id, m1.id, "hack")

    # ------------------------------------------------------------------ 3. Thu hoi
    m_recall = svc.send_message(db, off2, grp.id, ChatMessageCreate(content="Tin gửi nhầm"))
    r = svc.recall_message(db, off2, grp.id, m_recall.id)
    check("thu hoi tin cua minh -> is_recalled + noi dung rong", r.is_recalled and r.content == "")
    r2 = svc.recall_message(db, off2, grp.id, m_recall.id)
    check("thu hoi lai (idempotent) -> van is_recalled", r2.is_recalled)
    expect_http("sua tin da thu hoi -> 409", 409,
                svc.edit_message, db, off2, grp.id, m_recall.id, "x")
    expect_http("nguoi thuong thu hoi tin nguoi khac -> 403", 403,
                svc.recall_message, db, off1, grp.id, m2.id)

    # QTV nhom (khong phai chi huy) thu hoi tin thanh vien khac -> OK
    svc.set_member_admin(db, cmd, grp.id, off3.id, True)
    m_by_off1 = svc.send_message(db, off1, grp.id, ChatMessageCreate(content="Câu này sẽ bị QTV thu hồi"))
    r3 = svc.recall_message(db, off3, grp.id, m_by_off1.id)
    check("QTV nhom thu hoi tin thanh vien khac -> OK", r3.is_recalled)

    # ------------------------------------------------------------------ 4. Reaction
    react1 = svc.toggle_reaction(db, off1, grp.id, m2.id, "👍", add=True)
    check("tha reaction -> count 1, mine", react1.reactions and react1.reactions[0].count == 1 and react1.reactions[0].mine)
    react1b = svc.toggle_reaction(db, off1, grp.id, m2.id, "👍", add=True)
    check("tha lai cung reaction (idempotent) -> van count 1", react1b.reactions[0].count == 1)
    react2 = svc.toggle_reaction(db, off2, grp.id, m2.id, "🫡", add=True)
    total = {r.emoji: r.count for r in react2.reactions}
    check("2 loai emoji tren cung tin", total.get("👍") == 1 and total.get("🫡") == 1, str(total))
    react3 = svc.toggle_reaction(db, off1, grp.id, m2.id, "👍", add=False)
    check("go reaction -> khong con 👍", all(r.emoji != "👍" for r in react3.reactions))

    # ------------------------------------------------------------------ 5. Ghim
    pinned = svc.set_pin(db, cmd, grp.id, m2.id, True)
    check("chi huy ghim tin trong nhom -> is_pinned", pinned.is_pinned)
    plist = svc.list_pinned(db, off1, grp.id)
    check("list_pinned tra ve tin da ghim", len(plist) == 1 and plist[0].id == m2.id)
    expect_http("thanh vien thuong ghim tin trong nhom -> 403", 403,
                svc.set_pin, db, off2, grp.id, m1.id, True)
    dm = svc.send_message(db, off1, direct.id, ChatMessageCreate(content="ghim 1-1"))
    pin_direct = svc.set_pin(db, off1, direct.id, dm.id, True)
    check("1-1: mot ben ghim -> OK", pin_direct.is_pinned)
    svc.set_pin(db, cmd, grp.id, m2.id, False)
    check("bo ghim -> list_pinned rong", len(svc.list_pinned(db, off1, grp.id)) == 0)

    # ------------------------------------------------------------------ 6. Chuyen tiep
    fwd = svc.forward_message(db, off1, grp.id, m2.id, direct.id)
    check("chuyen tiep: forwarded_from duoc dinh kem", fwd.forwarded_from is not None and fwd.forwarded_from.id == m2.id)
    check("chuyen tiep: tin nam o hoi thoai dich", fwd.conversation_id == direct.id)
    expect_http("chuyen tiep toi hoi thoai khong phai thanh vien -> 403", 403,
                svc.forward_message, db, outsider, grp.id, m2.id, direct.id)
    expect_http("chuyen tiep tin da thu hoi -> 409", 409,
                svc.forward_message, db, off2, grp.id, m_recall.id, direct.id)

    # ------------------------------------------------------------------ 7. Tim kiem
    hits = svc.search_in_conversation(db, off1, grp.id, "SSCĐ")
    check("tim trong hoi thoai: co ket qua", len(hits) >= 1 and all("SSCĐ" in h.content for h in hits))
    check("tim trong hoi thoai: bo qua tin da thu hoi",
          all(not h.is_recalled for h in svc.search_in_conversation(db, off2, grp.id, "nhầm")))
    all_hits = svc.search_all(db, off1, "nhận")
    check("tim toan bo hoi thoai cua user", len(all_hits) >= 1)
    expect_http("tim trong hoi thoai khong phai thanh vien -> 403", 403,
                svc.search_in_conversation, db, outsider, grp.id, "x")

    # ------------------------------------------------------------------ 8. Doi ten nhom + tin he thong
    before_cnt = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == grp.id, ChatMessage.message_type == "system"
    ).count()
    renamed = svc.rename_group(db, cmd, grp.id, "Kíp trực A (đã kiện toàn)")
    after_cnt = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == grp.id, ChatMessage.message_type == "system"
    ).count()
    check("doi ten nhom -> ten moi", renamed.name == "Kíp trực A (đã kiện toàn)")
    check("doi ten nhom -> sinh 1 tin he thong", after_cnt == before_cnt + 1)
    expect_http("thanh vien thuong doi ten nhom -> 403", 403,
                svc.rename_group, db, off2, grp.id, "Tên trái phép")

    # ------------------------------------------------------------------ 9. Phong / go QTV nhom
    conv2 = svc.set_member_admin(db, cmd, grp.id, off1.id, True)
    check("phong QTV nhom -> is_admin trong participants",
          any(p.user_id == off1.id and p.is_admin for p in conv2.participants))
    conv3 = svc.set_member_admin(db, cmd, grp.id, off1.id, False)
    check("go QTV nhom -> het is_admin",
          any(p.user_id == off1.id and not p.is_admin for p in conv3.participants))
    expect_http("doi quyen nguoi tao nhom -> 409", 409,
                svc.set_member_admin, db, cmd, grp.id, cmd.id, False)
    expect_http("phong QTV nguoi ngoai nhom -> 404", 404,
                svc.set_member_admin, db, cmd, grp.id, outsider.id, True)
    expect_http("nguoi khong phai chi huy / nguoi tao phong QTV -> 403", 403,
                svc.set_member_admin, db, off2, grp.id, off1.id, True)

    # ------------------------------------------------------------------ 10. Tat thong bao / Luu tru
    svc.set_conversation_pref(db, off1, grp.id, muted=True)
    convs = {c.id: c for c in svc.list_user_conversations(db, off1)}
    check("tat thong bao -> is_muted trong list", convs[grp.id].is_muted)
    svc.set_conversation_pref(db, off1, grp.id, archived=True)
    ids_default = {c.id for c in svc.list_user_conversations(db, off1)}
    ids_arch = {c.id for c in svc.list_user_conversations(db, off1, include_archived=True)}
    check("luu tru -> an khoi danh sach mac dinh", grp.id not in ids_default)
    check("luu tru -> hien khi include_archived", grp.id in ids_arch)
    svc.set_conversation_pref(db, off1, grp.id, archived=False)

    # ------------------------------------------------------------------ 11. Bien nhan da doc
    svc.mark_as_read(db, off2, grp.id)
    receipts = {r.user_id: r for r in svc.get_read_receipts(db, off1, grp.id)}
    check("receipts: co moc doc cho tung thanh vien", off2.id in receipts and receipts[off2.id].last_read_message_id > 0)
    expect_http("receipts hoi thoai khong phai thanh vien -> 403", 403,
                svc.get_read_receipts, db, outsider, grp.id)

    # ------------------------------------------------------------------ 12. Tin he thong khi them / bo thanh vien
    emitted = []
    svc.add_member_to_group(db, cmd, grp.id, outsider.id, emitted=emitted)
    check("them thanh vien -> sinh tin he thong", len(emitted) == 1 and emitted[0].message_type == "system")
    emitted2 = []
    svc.remove_member_from_group(db, cmd, grp.id, outsider.id, emitted=emitted2)
    check("bo thanh vien -> sinh tin he thong", len(emitted2) == 1 and emitted2[0].message_type == "system")

    # ------------------------------------------------------------------ 13. Broadcast helpers khong loi khi khong co ket noi WS
    async def _smoke_broadcasts():
        await svc.broadcast_message_edit(db, grp.id, edited)
        await svc.broadcast_message_recall(db, grp.id, m_recall.id)
        await svc.broadcast_message_reaction(db, grp.id, react2)
        await svc.broadcast_message_pin(db, grp.id, m2.id, True)
        await svc.broadcast_read(db, grp.id, off1, 10)
        await svc.broadcast_typing(db, grp.id, off1)
        await svc.broadcast_presence(db, off1.id, True)

    try:
        asyncio.run(_smoke_broadcasts())
        check("broadcast helpers chay tron khi khong co WS connection", True)
    except Exception as e:  # noqa: BLE001
        check("broadcast helpers chay tron khi khong co WS connection", False, repr(e))

    db.close()
    print()
    print(f"PASS: {_PASS} | FAIL: {_FAIL}")
    if _FAIL:
        print("KET QUA: CO TEST THAT BAI")
        return 1
    print("KET QUA: TAT CA PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
