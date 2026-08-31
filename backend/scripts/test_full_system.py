"""Kiem thu tu dong End-to-End toan bo 5 Phase (API v1.3.0 -> v1.8.0).

Script tu khoi dong mot instance uvicorn rieng (cong 8099), goi API bang HTTP
that (urllib - khong can thu vien ngoai), in Pass/Fail + status code + du lieu
tra ve cho tung kich ban, roi don dep du lieu test va tat server.

Chay:
    backend/venv/Scripts/python.exe scripts/test_full_system.py
"""

import base64
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PORT = 8099
API = f"http://127.0.0.1:{PORT}"
TAG = time.strftime("%H%M%S")

PASS = 0
FAIL = 0
_SERVER: subprocess.Popen | None = None


# --------------------------------------------------------------------------- io
class Resp:
    def __init__(self, status: int, data):
        self.status = status
        self.data = data

    def __repr__(self):
        return f"<Resp {self.status}>"


def _multipart(fields: dict, files: list[tuple]) -> tuple[str, bytes]:
    boundary = "----e2e" + uuid.uuid4().hex
    b = boundary.encode()
    out: list[bytes] = []
    for k, v in fields.items():
        out += [b"--" + b, f'Content-Disposition: form-data; name="{k}"'.encode(), b"", str(v).encode()]
    for name, filename, content, ctype in files:
        out += [
            b"--" + b,
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode(),
            f"Content-Type: {ctype}".encode(),
            b"",
            content,
        ]
    out += [b"--" + b + b"--", b""]
    return boundary, b"\r\n".join(out)


def req(method: str, path: str, token: str | None = None, json_body=None, multipart=None) -> Resp:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    elif multipart is not None:
        fields, files = multipart
        boundary, data = _multipart(fields, files)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    r = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        status = e.code
    body = None
    if raw:
        try:
            body = json.loads(raw)
        except Exception:
            body = raw.decode("utf-8", "replace")
    return Resp(status, body)


def jwt_claims(token: str) -> dict:
    seg = token.split(".")[1]
    seg += "=" * (-len(seg) % 4)
    return json.loads(base64.urlsafe_b64decode(seg))


# --------------------------------------------------------------------- reporting
def ok(name: str, cond: bool, detail: str = "") -> bool:
    global PASS, FAIL
    if cond:
        PASS += 1
        mark = "PASS"
    else:
        FAIL += 1
        mark = "FAIL"
    print(f"  [{mark}] {name}" + (f"   {detail}" if detail else ""))
    return cond


def expect(name: str, resp: Resp, *allowed: int) -> Resp:
    cond = resp.status in allowed
    detail = f"HTTP {resp.status}"
    if not cond:
        detail += f" (mong doi {allowed}) :: {json.dumps(resp.data, ensure_ascii=False)[:200]}"
    ok(name, cond, detail)
    return resp


def show(label: str, data) -> None:
    txt = json.dumps(data, ensure_ascii=False)
    print(f"        -> {label}: {txt[:400]}{'...' if len(txt) > 400 else ''}")


def head(title: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


# ------------------------------------------------------------------ server boot
def start_server() -> None:
    global _SERVER
    _SERVER = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT), "--log-level", "warning"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for _ in range(60):
        if _SERVER.poll() is not None:
            out = _SERVER.stdout.read() if _SERVER.stdout else ""
            raise RuntimeError(f"uvicorn thoat som:\n{out}")
        try:
            with urllib.request.urlopen(API + "/", timeout=2) as r:
                if r.status == 200:
                    print(f"  uvicorn san sang tai {API}")
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("uvicorn khong phan hoi sau 30s")


def stop_server() -> None:
    if _SERVER is None:
        return
    _SERVER.terminate()
    try:
        _SERVER.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _SERVER.kill()


def cleanup_db() -> None:
    """Xoa du lieu test (theo prefix) truc tiep qua DB, thu tu an toan FK."""
    from sqlalchemy import text

    from app.core.database import engine

    stmts = [
        "DELETE FROM command_meeting_attendees WHERE meeting_id IN (SELECT id FROM command_meetings WHERE title LIKE 'E2E%')",
        "DELETE FROM command_meetings WHERE title LIKE 'E2E%'",
        "DELETE FROM dispatch_acknowledgements WHERE dispatch_id IN (SELECT id FROM official_dispatches WHERE dispatch_number LIKE 'E2E%')",
        "DELETE FROM official_dispatches WHERE dispatch_number LIKE 'E2E%'",
        "DELETE FROM command_thread_reads WHERE thread_id IN (SELECT id FROM command_threads WHERE title LIKE 'E2E%')",
        "DELETE FROM command_messages WHERE thread_id IN (SELECT id FROM command_threads WHERE title LIKE 'E2E%')",
        "DELETE FROM command_threads WHERE title LIKE 'E2E%'",
        "DELETE FROM directive_submissions WHERE target_id IN (SELECT t.id FROM directive_assignment_targets t JOIN directive_assignments a ON a.id=t.assignment_id WHERE a.title LIKE 'E2E%')",
        "DELETE FROM directive_assignment_targets WHERE assignment_id IN (SELECT id FROM directive_assignments WHERE title LIKE 'E2E%')",
        "DELETE FROM directive_assignments WHERE title LIKE 'E2E%'",
        "DELETE FROM directive_thread_reads WHERE thread_id IN (SELECT id FROM directive_threads WHERE title LIKE 'E2E%')",
        "DELETE FROM directive_messages WHERE thread_id IN (SELECT id FROM directive_threads WHERE title LIKE 'E2E%')",
        "DELETE FROM directive_threads WHERE title LIKE 'E2E%'",
        "DELETE FROM users WHERE username LIKE 'e2e%'",
        "DELETE FROM units WHERE name LIKE 'E2E%'",
    ]
    with engine.begin() as conn:
        for s in stmts:
            try:
                conn.execute(text(s))
            except Exception as e:  # noqa: BLE001
                print(f"  (cleanup bo qua) {s[:60]}... : {e}")
    print("  Da don dep du lieu test.")


PDF = ("bao_cao.pdf", b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n", "application/pdf")
DOCX = ("tai_lieu.docx", b"PK\x03\x04 e2e docx placeholder", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# =========================================================================== #
def main() -> None:
    ctx: dict = {}

    # ------------------------------------------------------------------ PHASE 1
    head("PHASE 1 - Nen tang: dang nhap admin, don vi, doi mat khau, phan quyen")

    r = expect("POST /users/login (admin/admin)", req("POST", "/users/login", json_body={"username": "admin", "password": "admin"}), 200)
    admin = r.data["access_token"]
    cl = jwt_claims(admin)
    show("claim admin", {k: cl.get(k) for k in ("sub", "role", "adm", "clr", "mcp")})
    ok("admin co role=admin & adm=true & clr=true", cl.get("role") == "admin" and cl.get("adm") and cl.get("clr"))
    ctx["admin"] = admin

    unit_name = f"E2E-TiepDoan-{TAG}"
    r = expect("POST /units/ (tao don vi)", req("POST", "/units/", admin, {"name": unit_name, "unit_kind": "tieu_doan"}), 201)
    show("unit", r.data)
    unit_id = r.data["id"]
    ctx["unit_id"] = unit_id

    r = expect("POST /units/ trung ten -> 409", req("POST", "/units/", admin, {"name": unit_name, "unit_kind": "tieu_doan"}), 409)

    off_u = f"e2e{TAG}off"
    r = expect(
        "POST /users/ (tao officer + unit + directive_channel_access)",
        req("POST", "/users/", admin, {
            "username": off_u, "password": "E2ePass123", "full_name": f"CB E2E {TAG}",
            "role": "officer", "unit_id": unit_id, "directive_channel_access": True,
        }),
        201,
    )
    show("officer", {k: r.data[k] for k in ("id", "username", "role", "unit_id", "unit_name", "directive_channel_access", "must_change_password")})
    off_id = r.data["id"]
    ok("officer must_change_password = true (tai khoan do admin cap)", r.data["must_change_password"] is True)
    ok("officer unit_name join dung", r.data["unit_name"] == unit_name)

    expect("POST /users/ mat khau yeu -> 422", req("POST", "/users/", admin, {"username": f"e2e{TAG}w", "password": "abcdefgh", "full_name": "x", "role": "officer"}), 422)
    expect("POST /users/ username sai dinh dang -> 422", req("POST", "/users/", admin, {"username": f"E2E {TAG}", "password": "E2ePass123", "full_name": "x", "role": "officer"}), 422)

    r = expect("POST /users/login (officer, mat khau tam)", req("POST", "/users/login", json_body={"username": off_u, "password": "E2ePass123"}), 200)
    off_tmp = r.data["access_token"]
    ok("token officer co mcp=true", jwt_claims(off_tmp).get("mcp") is True)
    expect("officer POST /units/ -> 403 (khong du quyen)", req("POST", "/units/", off_tmp, {"name": "x", "unit_kind": "tram"}), 403)

    expect("POST /profile/change-password (officer doi mat khau lan dau) -> 204", req("POST", "/profile/change-password", off_tmp, {"current_password": "E2ePass123", "new_password": "E2eNew456"}), 204)
    r = expect("POST /users/login (officer, mat khau moi)", req("POST", "/users/login", json_body={"username": off_u, "password": "E2eNew456"}), 200)
    off = r.data["access_token"]
    ok("token officer sau doi mat khau: mcp=false", jwt_claims(off).get("mcp") is False)
    ctx["off"] = off
    ctx["off_id"] = off_id
    ctx["off_username"] = off_u

    # clearance officer + plain officer (cho Phase 4/5)
    clr_u = f"e2e{TAG}clr"
    r = expect("POST /users/ (officer se cap clearance)", req("POST", "/users/", admin, {"username": clr_u, "password": "E2ePass123", "full_name": f"CB MAT {TAG}", "role": "officer"}), 201)
    clr_id = r.data["id"]
    expect("PATCH /users/{id}/clearance {true} -> 200", req("PATCH", f"/users/{clr_id}/clearance", admin, {"clearance": True}), 200)
    r = expect("POST /users/login (clearance officer)", req("POST", "/users/login", json_body={"username": clr_u, "password": "E2ePass123"}), 200)
    clr = r.data["access_token"]
    ok("token clearance officer co clr=true", jwt_claims(clr).get("clr") is True)
    ctx["clr"] = clr
    ctx["clr_id"] = clr_id

    plain_u = f"e2e{TAG}plain"
    r = expect("POST /users/ (officer khong clearance)", req("POST", "/users/", admin, {"username": plain_u, "password": "E2ePass123", "full_name": f"CB thuong {TAG}", "role": "officer"}), 201)
    r = expect("POST /users/login (plain officer)", req("POST", "/users/login", json_body={"username": plain_u, "password": "E2ePass123"}), 200)
    plain = r.data["access_token"]
    ok("token plain officer clr=false", jwt_claims(plain).get("clr") is False)
    ctx["plain"] = plain

    r = expect("POST /users/{id}/reset-password -> 204", req("POST", f"/users/{clr_id}/reset-password", admin, {"new_password": "E2eReset789"}), 204)
    r = expect("GET /users/{id} sau reset", req("GET", f"/users/{clr_id}", admin), 200)
    ok("reset-password dat must_change_password=true", r.data["must_change_password"] is True)

    # ------------------------------------------------------------------ PHASE 2
    head("PHASE 2 - Chi dao & Bao cao: luong trao doi, tin nhan + file, danh dau da doc")

    expect("plain officer GET /directive-threads -> 403", req("GET", "/directive-threads", ctx["plain"]), 403)

    r = expect(
        "officer POST /directive-threads (tao luong cho don vi minh)",
        req("POST", "/directive-threads", off, {"unit_id": 99999, "title": f"E2E Bao cao tuan {TAG}"}),
        201,
    )
    show("thread", r.data)
    tid = r.data["id"]
    ok("unit_id bi ep ve don vi cua officer", r.data["unit_id"] == unit_id)
    ctx["tid"] = tid

    r = expect("admin GET /directive-threads (scope all -> thay luong)", req("GET", "/directive-threads", admin), 200)
    ok("admin thay luong vua tao", any(t["id"] == tid for t in r.data))

    r = expect(
        "admin POST message + dinh kem PDF",
        req("POST", f"/directive-threads/{tid}/messages", admin, multipart=({"body": "Yeu cau don vi bao cao truoc 16h"}, [("file", *PDF)])),
        201,
    )
    show("message", {k: r.data[k] for k in ("id", "sender_full_name", "body", "attachment_url")})
    ok("message co attachment_url /static/directive/", str(r.data["attachment_url"]).startswith("/static/directive/"))

    r = expect("officer GET /directive-threads/{id} (danh dau da doc)", req("GET", f"/directive-threads/{tid}", off), 200)
    ok("officer message_count = 1", r.data["message_count"] == 1)
    r = expect("officer GET /directive-threads (unread sau khi doc)", req("GET", "/directive-threads", off), 200)
    my = next(t for t in r.data if t["id"] == tid)
    ok("unread_count = 0 sau khi doc", my["unread_count"] == 0, f"unread={my['unread_count']}")

    expect("officer POST message tra loi", req("POST", f"/directive-threads/{tid}/messages", off, multipart=({"body": "Don vi da nhan, se bao cao dung han"}, [])), 201)
    expect("admin POST them 1 message", req("POST", f"/directive-threads/{tid}/messages", admin, multipart=({"body": "Bo sung: kem so lieu quan so"}, [])), 201)
    r = expect("officer GET /directive-threads (unread tang)", req("GET", "/directive-threads", off), 200)
    my = next(t for t in r.data if t["id"] == tid)
    ok("unread_count = 1 (theo last_read_message_id)", my["unread_count"] == 1, f"unread={my['unread_count']}")

    expect("officer PATCH close -> 403 (chi BCH)", req("PATCH", f"/directive-threads/{tid}/close", off, {"is_closed": True}), 403)
    expect("admin PATCH close -> 200", req("PATCH", f"/directive-threads/{tid}/close", admin, {"is_closed": True}), 200)
    expect("post sau khi dong -> 409", req("POST", f"/directive-threads/{tid}/messages", admin, multipart=({"body": "muon"}, [])), 409)

    # ------------------------------------------------------------------ PHASE 3
    head("PHASE 3 - Giao nhiem vu: assignment + target don vi + nop bao cao + duyet/tra lai")

    r = expect(
        "admin POST /directive-assignments (target = don vi officer)",
        req("POST", "/directive-assignments", admin, {
            "title": f"E2E Bao cao huan luyen {TAG}", "description": "Nop truoc 16h",
            "due_date": "2026-12-31", "targets": [{"unit_id": unit_id}],
        }),
        201,
    )
    show("assignment", {k: r.data[k] for k in ("id", "status", "target_count", "pending_count")})
    aid = r.data["id"]
    ctx["aid"] = aid
    ok("assignment status = dang_thuc_hien", r.data["status"] == "dang_thuc_hien")

    r = expect("officer GET /directive-assignments (thay nhiem vu cua minh)", req("GET", "/directive-assignments", off), 200)
    ok("officer thay assignment", any(a["id"] == aid for a in r.data))
    r = expect("officer GET /directive-assignments/{id}", req("GET", f"/directive-assignments/{aid}", off), 200)
    ok("officer chi thay 1 target (cua don vi minh)", r.data["target_count"] == 1)
    tgt = r.data["targets"][0]["id"]

    expect("officer submit thieu content -> 422", req("POST", f"/directive-assignments/{aid}/targets/{tgt}/submit", off, multipart=({}, [])), 422)
    r = expect(
        "officer POST submit bao cao + file DOCX",
        req("POST", f"/directive-assignments/{aid}/targets/{tgt}/submit", off, multipart=({"content": "Da hoan thanh 80%"}, [("file", *DOCX)])),
        201,
    )
    show("target sau submit", {k: r.data[k] for k in ("status", "submission_count")})
    ok("target status = cho_duyet", r.data["status"] == "cho_duyet")
    ok("submission co attachment_url /static/documents/", str(r.data["submissions"][-1]["attachment_url"]).startswith("/static/documents/"))

    expect("officer review -> 403", req("POST", f"/directive-assignments/{aid}/targets/{tgt}/review", off, {"result": "da_duyet"}), 403)
    r = expect("admin review -> tra_lai", req("POST", f"/directive-assignments/{aid}/targets/{tgt}/review", admin, {"result": "tra_lai", "review_note": "Bo sung so lieu quan so"}), 200)
    ok("target status = tra_lai", r.data["status"] == "tra_lai")
    expect("admin review lai (dang tra_lai) -> 409", req("POST", f"/directive-assignments/{aid}/targets/{tgt}/review", admin, {"result": "da_duyet"}), 409)

    expect("officer nop lai bao cao", req("POST", f"/directive-assignments/{aid}/targets/{tgt}/submit", off, multipart=({"content": "Da bo sung so lieu quan so"}, [])), 201)
    r = expect("admin duyet -> da_duyet", req("POST", f"/directive-assignments/{aid}/targets/{tgt}/review", admin, {"result": "da_duyet"}), 200)
    ok("target status = da_duyet", r.data["status"] == "da_duyet")
    r = expect("admin GET assignment -> hoan_thanh", req("GET", f"/directive-assignments/{aid}", admin), 200)
    ok("assignment status = hoan_thanh (tat ca target da duyet)", r.data["status"] == "hoan_thanh")
    expect("officer submit sau khi da_duyet -> 409", req("POST", f"/directive-assignments/{aid}/targets/{tgt}/submit", off, multipart=({"content": "muon"}, [])), 409)

    # ------------------------------------------------------------------ PHASE 4
    head("PHASE 4 - Kenh chuyen BCH & Cong van: RBAC clearance, so cong van, ky nhan")

    expect("plain officer GET /command-threads -> 403", req("GET", "/command-threads", ctx["plain"]), 403)
    expect("clearance officer GET /command-threads -> 200", req("GET", "/command-threads", clr), 200)
    expect("plain officer GET /official-dispatches -> 403", req("GET", "/official-dispatches", ctx["plain"]), 403)

    dn = f"E2E-{TAG}/CV-BTL"
    r = expect(
        "admin POST /official-dispatches (van ban den + file PDF)",
        req("POST", "/official-dispatches", admin, multipart=(
            {"direction": "den", "dispatch_number": dn, "summary": "V/v trien khai nhiem vu SSCD",
             "issuing_org": "Bo Tu lenh", "receiving_org": "Lu doan 21", "issued_date": "2026-08-20", "status": "moi"},
            [("file", *PDF)],
        )),
        201,
    )
    show("dispatch", {k: r.data[k] for k in ("id", "direction", "dispatch_number", "status", "recipient_count", "acknowledged_count")})
    did = r.data["id"]
    ctx["did"] = did
    expect("admin POST trung so hieu -> 409", req("POST", "/official-dispatches", admin, multipart=({"direction": "den", "dispatch_number": dn, "summary": "x"}, [])), 409)
    expect("clearance officer POST (khong phai BCH) -> 403", req("POST", "/official-dispatches", clr, multipart=({"direction": "di", "dispatch_number": f"E2E-{TAG}-x", "summary": "x"}, [])), 403)

    expect("clearance officer GET /official-dispatches -> 200", req("GET", "/official-dispatches", clr), 200)
    r = expect("clearance officer GET /official-dispatches/{id}", req("GET", f"/official-dispatches/{did}", clr), 200)
    show("ack summary", {"acknowledged": r.data["acknowledged_count"], "pending": len(r.data["pending"])})

    r = expect("clearance officer POST /acknowledge (ky nhan + phan hoi)", req("POST", f"/official-dispatches/{did}/acknowledge", clr, {"response_note": "Da quan triet, trien khai toi dai doi"}), 200)
    ok("acknowledged_count = 1 sau ky nhan", r.data["acknowledged_count"] == 1)
    r = expect("clearance officer POST /acknowledge lan 2 (upsert note)", req("POST", f"/official-dispatches/{did}/acknowledge", clr, {"response_note": "Cap nhat: hoan thanh 50%"}), 200)
    acked = next((a for a in r.data["acknowledged"] if a["user_id"] == clr_id), None)
    ok("upsert cap nhat response_note", acked and acked["response_note"] == "Cap nhat: hoan thanh 50%")

    expect("plain officer POST /acknowledge -> 403", req("POST", f"/official-dispatches/{did}/acknowledge", ctx["plain"], {}), 403)
    expect("clearance officer GET /download -> 200", req("GET", f"/official-dispatches/{did}/download", clr), 200)
    expect("plain officer GET /download -> 403", req("GET", f"/official-dispatches/{did}/download", ctx["plain"]), 403)
    expect("admin PUT cap nhat status -> da_xu_ly", req("PUT", f"/official-dispatches/{did}", admin, multipart=(
        {"direction": "den", "dispatch_number": dn, "summary": "V/v trien khai nhiem vu SSCD (da xu ly)", "status": "da_xu_ly"}, [])), 200)

    # ------------------------------------------------------------------ PHASE 5
    head("PHASE 5 - Giao ban truc tuyen: cuoc hop, diem danh thanh phan, bien ban ket luan")

    r = expect(
        "admin POST /command-meetings (co thanh phan trieu tap)",
        req("POST", "/command-meetings", admin, {
            "title": f"E2E Giao ban tuan {TAG}", "start_time": "2026-09-02T08:00:00",
            "end_time": "2026-09-02T10:00:00", "location": "Phong hop A",
            "meeting_link": "https://meet.example/e2e", "agenda": "1. Danh gia SSCD\n2. Trien khai nhiem vu",
            "attendee_user_ids": [clr_id],
        }),
        201,
    )
    show("meeting", {k: r.data[k] for k in ("id", "status", "attendee_count", "present_count")})
    mid = r.data["id"]
    ctx["mid"] = mid

    expect("end_time < start_time -> 400", req("POST", "/command-meetings", admin, {"title": "x", "start_time": "2026-09-02T10:00:00", "end_time": "2026-09-02T08:00:00"}), 400)
    expect("start_time sai dinh dang -> 422", req("POST", "/command-meetings", admin, {"title": "x", "start_time": "khong-phai-ngay"}), 422)

    expect("clearance officer GET /command-meetings/{id} -> 200", req("GET", f"/command-meetings/{mid}", clr), 200)
    expect("plain officer GET /command-meetings/{id} -> 403", req("GET", f"/command-meetings/{mid}", ctx["plain"]), 403)
    expect("clearance officer POST /command-meetings -> 403 (khong phai BCH)", req("POST", "/command-meetings", clr, {"title": "x", "start_time": "2026-09-02T08:00:00"}), 403)

    r = expect("admin PATCH diem danh clearance officer = co_mat", req("PATCH", f"/command-meetings/{mid}/attendees/{clr_id}", admin, {"attendance": "co_mat"}), 200)
    ok("attendee status = co_mat", r.data["attendance"] == "co_mat")
    r = expect("clearance officer PATCH y kien dong gop (chinh minh)", req("PATCH", f"/command-meetings/{mid}/attendees/{clr_id}", clr, {"contribution_note": "De nghi tang cuong truc dem"}), 200)
    ok("contribution_note luu dung", r.data["contribution_note"] == "De nghi tang cuong truc dem")
    expect("clearance officer PATCH diem danh nguoi khac -> 403", req("PATCH", f"/command-meetings/{mid}/attendees/1", clr, {"attendance": "co_mat"}), 403)

    expect("clearance officer POST /minutes -> 403", req("POST", f"/command-meetings/{mid}/minutes", clr, {"minutes": "x"}), 403)
    r = expect("admin POST /minutes (+ mark_finished)", req("POST", f"/command-meetings/{mid}/minutes", admin, {"minutes": "Ket luan: hoan thanh tot cac noi dung.", "mark_finished": True}), 200)
    ok("meeting status = da_ket_thuc", r.data["status"] == "da_ket_thuc")
    ok("minutes da luu", "Ket luan" in (r.data["minutes"] or ""))

    r = expect("admin POST /attachment (tai lieu hop DOCX)", req("POST", f"/command-meetings/{mid}/attachment", admin, multipart=({}, [("file", *DOCX)])), 200)
    ok("meeting co attachment_url", bool(r.data["attachment_url"]))
    expect("clearance officer GET /command-meetings/{id}/download -> 200", req("GET", f"/command-meetings/{mid}/download", clr), 200)
    expect("plain officer GET /download -> 403", req("GET", f"/command-meetings/{mid}/download", ctx["plain"]), 403)

    r = expect("admin POST /attendees (moi them admin)", req("POST", f"/command-meetings/{mid}/attendees", admin, {"user_ids": [1]}), 201)
    ok("attendee_count = 2", r.data["attendee_count"] == 2)
    expect("admin POST /attendees trung -> 409", req("POST", f"/command-meetings/{mid}/attendees", admin, {"user_ids": [clr_id]}), 409)
    expect("admin DELETE /attendees/1 -> 204", req("DELETE", f"/command-meetings/{mid}/attendees/1", admin), 204)
    expect("admin DELETE /command-meetings/{id} -> 204", req("DELETE", f"/command-meetings/{mid}", admin), 204)
    expect("GET /command-meetings/{id} sau xoa -> 404", req("GET", f"/command-meetings/{mid}", admin), 404)


if __name__ == "__main__":
    print("KIEM THU E2E TOAN BO 5 PHASE  |  tag =", TAG)
    err = None
    try:
        start_server()
        main()
    except Exception as e:  # noqa: BLE001
        import traceback

        err = e
        print("\n!!! LOI KHI CHAY KICH BAN:")
        traceback.print_exc()
    finally:
        head("DON DEP")
        try:
            cleanup_db()
        except Exception as e:  # noqa: BLE001
            print("  cleanup loi:", e)
        stop_server()

    head("KET QUA")
    total = PASS + FAIL
    print(f"  Tong: {total}   |   PASS: {PASS}   |   FAIL: {FAIL}")
    if err is not None:
        print("  => KICH BAN DUNG GIUA CHUNG DO LOI.")
        sys.exit(2)
    sys.exit(0 if FAIL == 0 else 1)
