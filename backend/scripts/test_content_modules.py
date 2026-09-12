"""Kiem thu tu dong End-to-End cac phan he NOI DUNG (API content modules).

Phu 5 nhom route trong app/api/routes/:
    - posts.py                (Tin bai)      : tao, duyet/xuat ban, phan quyen xem, sua, xoa, anh bia
    - announcements.py        (Thong bao)    : tao, ghim, cong khai, uu tien, han hieu luc (ends_at)
    - documents.py            (Tai lieu)     : tai len, tai ve, phan quyen theo bac, sua meta, xoa
    - education_materials.py   (GD chinh tri): tao, ky/thoi han (period_label), dinh kem, phan quyen
    - home.py                 (Trang chu)    : /home/public (khach) + /home/summary (da dang nhap)

Ke thua dung chuan cua scripts/test_full_system.py: tu khoi dong uvicorn rieng
(cong 8098), goi API bang HTTP that (urllib - khong can thu vien ngoai), in
Pass/Fail + status code cho tung kich ban, roi TU DON DEP toan bo du lieu test
khoi MySQL va tat server.

Chay:
    backend/venv/Scripts/python.exe scripts/test_content_modules.py
    hoac:  python -m scripts.test_content_modules
"""

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

PORT = 8098
API = f"http://127.0.0.1:{PORT}"
TAG = time.strftime("%H%M%S")

# Tien to nhan dien du lieu test (dung cho ca dat ten lan don dep).
UPREFIX = f"e2ec{TAG}"          # username
TPREFIX = f"E2EC-{TAG}"        # title / tieu de moi entity noi dung

PASS = 0
FAIL = 0
_SERVER: "subprocess.Popen | None" = None


# --------------------------------------------------------------------------- io
class Resp:
    def __init__(self, status: int, data):
        self.status = status
        self.data = data

    def __repr__(self):
        return f"<Resp {self.status}>"


def _multipart(fields: dict, files: list) -> "tuple[str, bytes]":
    boundary = "----e2ec" + uuid.uuid4().hex
    b = boundary.encode()
    out: list = []
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


def req(method: str, path: str, token: "str | None" = None, json_body=None, multipart=None) -> Resp:
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


def titles(rows) -> list:
    return [r.get("title") for r in rows] if isinstance(rows, list) else []


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
    """Xoa sach du lieu test (theo tien to) truc tiep qua DB, thu tu an toan FK."""
    from sqlalchemy import text

    from app.core.database import engine

    stmts = [
        f"DELETE FROM posts WHERE title LIKE '{TPREFIX}%'",
        f"DELETE FROM announcements WHERE title LIKE '{TPREFIX}%'",
        f"DELETE FROM documents WHERE title LIKE '{TPREFIX}%'",
        f"DELETE FROM education_materials WHERE title LIKE '{TPREFIX}%'",
        f"DELETE FROM users WHERE username LIKE '{UPREFIX}%'",
        f"DELETE FROM units WHERE name LIKE '{TPREFIX}%'",
    ]
    with engine.begin() as conn:
        for s in stmts:
            try:
                res = conn.execute(text(s))
                print(f"  {s[:60]}...  -> {res.rowcount} dong")
            except Exception as e:  # noqa: BLE001
                print(f"  (cleanup bo qua) {s[:60]}... : {e}")
    print("  Da don dep du lieu test.")


PDF = ("bao_cao.pdf", b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n", "application/pdf")
PNG = ("anh_bia.png", b"\x89PNG\r\n\x1a\n" + b"e2ec png placeholder" * 4, "image/png")


# Ten vai tro cu -> so nguyen 0..5 (openapi >= v5.0.0). "soldier" cu = role 5 (chi xem).
_ROLE_INT = {"officer": 4, "commander": 1, "soldier": 5}


def mk_user(admin: str, suffix: str, role: str, unit_id: int, clearance: bool = False) -> dict:
    """Tao tai khoan test qua API va tra ve {id, username, token}."""
    uname = UPREFIX + suffix
    r = req("POST", "/users/", admin, {
        "username": uname, "password": "E2ecPass123", "full_name": f"{role.upper()} {TAG} {suffix}",
        "role": _ROLE_INT.get(role, role),
        "rank": "Thiếu tá", "position": f"Trợ lý {suffix}", "unit_id": unit_id,
    })
    assert r.status == 201, f"tao user {uname} that bai: {r.status} {r.data}"
    uid = r.data["id"]
    if clearance:
        rc = req("PATCH", f"/users/{uid}/clearance", admin, {"clearance": True})
        assert rc.status == 200, f"cap clearance that bai: {rc.data}"
    rl = req("POST", "/users/login", json_body={"username": uname, "password": "E2ecPass123"})
    assert rl.status == 200, f"login {uname} that bai: {rl.data}"
    return {"id": uid, "username": uname, "token": rl.data["access_token"]}


# =========================================================================== #
def main() -> None:
    # ---------------------------------------------------------------- CHUAN BI
    head("CHUAN BI - dang nhap admin, tao officer/officer2/commander/soldier/clearance")

    r = expect("POST /users/login (admin/admin)", req("POST", "/users/login", json_body={"username": "admin", "password": "admin"}), 200)
    admin = r.data["access_token"]

    # Don vi cho cac tai khoan test (unit_id BAT BUOC khi tao tai khoan).
    ru = req("POST", "/units/", admin, {"name": f"{TPREFIX} DonVi", "unit_kind": "tieu_doan"})
    assert ru.status == 201, f"tao don vi test that bai: {ru.status} {ru.data}"
    unit_id = ru.data["id"]

    off = mk_user(admin, "off", "officer", unit_id)
    off2 = mk_user(admin, "of2", "officer", unit_id)
    cmd = mk_user(admin, "cmd", "commander", unit_id)
    sol = mk_user(admin, "sol", "soldier", unit_id)
    clr = mk_user(admin, "clr", "officer", unit_id, clearance=True)
    for lbl, u in (("officer", off), ("officer2", off2), ("commander", cmd), ("soldier", sol), ("clearance officer", clr)):
        ok(f"tao {lbl} #{u['id']} + login OK", bool(u["token"]))

    A = off["token"]      # tac gia chinh
    B = off2["token"]     # officer khac -> kiem tra rule so huu
    C = cmd["token"]      # commander -> duyet / xoa bat ky
    S = sol["token"]      # soldier -> chi xem
    L = clr["token"]      # officer co clearance -> noi dung MAT

    # ============================================================== MODULE 1
    head("MODULE 1 - POSTS: tao, luong duyet, phan quyen xem theo bac, sua, anh bia, xoa")

    r = expect("officer POST /posts (cong_khai) -> cho_duyet",
               req("POST", "/posts", A, {"title": f"{TPREFIX} Post CongKhai", "category": "huan_luyen",
                                         "content": "noi dung ck", "classification": "cong_khai"}), 201)
    p_ck = r.data["id"]
    ok("officer dang bai -> status = cho_duyet", r.data["status"] == "cho_duyet", f"status={r.data['status']}")
    ok("PostOut co author_full_name", bool(r.data.get("author_full_name")))

    r = expect("officer POST /posts (noi_bo) -> cho_duyet",
               req("POST", "/posts", A, {"title": f"{TPREFIX} Post NoiBo", "category": "dan_van",
                                         "content": "noi dung nb", "classification": "noi_bo"}), 201)
    p_nb = r.data["id"]

    r = expect("commander POST /posts (cong_khai, featured) -> da_duyet ngay",
               req("POST", "/posts", C, {"title": f"{TPREFIX} Post Commander", "category": "khen_thuong",
                                         "content": "noi dung cmd", "classification": "cong_khai", "is_featured": True}), 201)
    p_cmd = r.data["id"]
    ok("commander dang bai -> status = da_duyet", r.data["status"] == "da_duyet", f"status={r.data['status']}")

    expect("soldier POST /posts -> 403 (khong du quyen)",
           req("POST", "/posts", S, {"title": f"{TPREFIX} x", "category": "huan_luyen", "content": "x"}), 403)
    expect("officer (khong clearance) POST /posts classification=mat -> 403",
           req("POST", "/posts", A, {"title": f"{TPREFIX} x", "category": "huan_luyen", "content": "x", "classification": "mat"}), 403)

    r = expect("clearance officer POST /posts (mat) -> 201 / cho_duyet",
               req("POST", "/posts", L, {"title": f"{TPREFIX} Post MAT", "category": "huan_luyen",
                                         "content": "noi dung mat", "classification": "mat"}), 201)
    p_mat = r.data["id"]
    ok("bai MAT vao hang cho_duyet", r.data["status"] == "cho_duyet")

    # --- phan quyen xem danh sach ---
    r = expect("GUEST GET /posts", req("GET", "/posts"), 200)
    g = titles(r.data)
    ok("guest thay bai da_duyet + cong_khai", f"{TPREFIX} Post Commander" in g)
    ok("guest KHONG thay bai cho_duyet", f"{TPREFIX} Post CongKhai" not in g)
    ok("guest KHONG thay bai noi_bo", f"{TPREFIX} Post NoiBo" not in g)
    ok("guest KHONG thay bai MAT", f"{TPREFIX} Post MAT" not in g)

    r = expect("SOLDIER GET /posts", req("GET", "/posts", S), 200)
    s = titles(r.data)
    ok("soldier thay bai da_duyet cong_khai", f"{TPREFIX} Post Commander" in s)
    ok("soldier KHONG thay bai cho_duyet cua officer", f"{TPREFIX} Post CongKhai" not in s)
    ok("soldier KHONG thay bai MAT", f"{TPREFIX} Post MAT" not in s)

    r = expect("OFFICER (tac gia) GET /posts", req("GET", "/posts", A), 200)
    a = titles(r.data)
    ok("officer thay moi bai cua chinh minh (ke ca cho_duyet)",
       f"{TPREFIX} Post CongKhai" in a and f"{TPREFIX} Post NoiBo" in a)
    ok("officer thay bai da_duyet cua nguoi khac", f"{TPREFIX} Post Commander" in a)

    r = expect("OFFICER2 GET /posts", req("GET", "/posts", B), 200)
    b = titles(r.data)
    ok("officer2 KHONG thay bai cho_duyet cua officer1", f"{TPREFIX} Post CongKhai" not in b)
    ok("officer2 thay bai da_duyet cong_khai", f"{TPREFIX} Post Commander" in b)

    r = expect("COMMANDER GET /posts", req("GET", "/posts", C), 200)
    cc = titles(r.data)
    ok("commander thay tat ca 4 bai test",
       all(t in cc for t in (f"{TPREFIX} Post CongKhai", f"{TPREFIX} Post NoiBo", f"{TPREFIX} Post Commander", f"{TPREFIX} Post MAT")))
    r = expect("COMMANDER GET /posts?status_filter=cho_duyet", req("GET", "/posts?status_filter=cho_duyet&limit=200", C), 200)
    cf = titles(r.data)
    ok("loc cho_duyet: co bai cho, khong co bai da_duyet",
       f"{TPREFIX} Post CongKhai" in cf and f"{TPREFIX} Post Commander" not in cf)

    # --- xem chi tiet ---
    expect("GUEST GET /posts/{noi_bo} -> 404 (khong lo ton tai)", req("GET", f"/posts/{p_nb}"), 404)
    expect("GUEST GET /posts/{da_duyet cong_khai} -> 200", req("GET", f"/posts/{p_cmd}"), 200)
    expect("SOLDIER GET /posts/{mat} -> 404", req("GET", f"/posts/{p_mat}", S), 404)
    expect("clearance officer GET /posts/{mat} -> 200", req("GET", f"/posts/{p_mat}", L), 200)

    # --- luong duyet ---
    expect("officer POST /posts/{id}/review -> 403 (chi commander)",
           req("POST", f"/posts/{p_nb}/review", A, {"status": "da_duyet"}), 403)
    r = expect("commander POST /posts/{id}/review {da_duyet} -> 200",
               req("POST", f"/posts/{p_ck}/review", C, {"status": "da_duyet"}), 200)
    ok("bai chuyen sang da_duyet", r.data["status"] == "da_duyet")

    r = expect("officer PUT /posts/{id} (sua bai da duyet cua minh) -> 200",
               req("PUT", f"/posts/{p_ck}", A, {"title": f"{TPREFIX} Post CongKhai", "category": "huan_luyen",
                                                "content": "noi dung ck (da sua)", "classification": "cong_khai"}), 200)
    ok("officer sua bai da_duyet -> tu ve cho_duyet", r.data["status"] == "cho_duyet", f"status={r.data['status']}")

    r = expect("commander POST review {tra_lai} + review_note -> 200",
               req("POST", f"/posts/{p_ck}/review", C, {"status": "tra_lai", "review_note": "Bo sung so lieu"}), 200)
    ok("status = tra_lai, luu review_note", r.data["status"] == "tra_lai" and r.data["review_note"] == "Bo sung so lieu")

    # --- anh bia ---
    r = expect("officer POST /posts/{id}/thumbnail (PNG) -> 200",
               req("POST", f"/posts/{p_ck}/thumbnail", A, multipart=({}, [("file", *PNG)])), 200)
    ok("cover_image_url = /static/posts/...", str(r.data.get("cover_image_url", "")).startswith("/static/posts/"))
    expect("officer POST /posts/{id}/thumbnail (PDF - sai dinh dang) -> 400",
           req("POST", f"/posts/{p_ck}/thumbnail", A, multipart=({}, [("file", *PDF)])), 400)

    # --- xoa ---
    expect("officer2 DELETE /posts/{id} cua officer1 -> 403", req("DELETE", f"/posts/{p_ck}", B), 403)
    expect("officer1 DELETE /posts/{id} cua minh -> 204", req("DELETE", f"/posts/{p_ck}", A), 204)
    expect("GET /posts/{id} sau xoa -> 404", req("GET", f"/posts/{p_ck}", C), 404)
    expect("commander DELETE /posts/{noi_bo cua officer} -> 204", req("DELETE", f"/posts/{p_nb}", C), 204)
    expect("commander DELETE /posts/{mat} -> 204", req("DELETE", f"/posts/{p_mat}", C), 204)
    expect("commander DELETE /posts/{commander} -> 204", req("DELETE", f"/posts/{p_cmd}", C), 204)

    # ============================================================== MODULE 2
    head("MODULE 2 - ANNOUNCEMENTS: tao, ghim, cong khai, uu tien, han hieu luc (ends_at)")

    r = expect("officer POST /announcements (is_public) -> 201",
               req("POST", "/announcements", A, {"title": f"{TPREFIX} TB CongKhai", "content": "thong bao mo",
                                                 "priority": "binh_thuong", "is_public": True}), 201)
    n_pub = r.data["id"]
    r = expect("officer POST /announcements (is_pinned) -> 201",
               req("POST", "/announcements", A, {"title": f"{TPREFIX} TB Ghim", "content": "ghim", "is_pinned": True}), 201)
    n_pin = r.data["id"]
    r = expect("officer POST /announcements (priority=khan) -> 201",
               req("POST", "/announcements", A, {"title": f"{TPREFIX} TB Khan", "content": "khan", "priority": "khan"}), 201)
    n_khan = r.data["id"]
    r = expect("officer POST /announcements (ends_at qua khu) -> 201",
               req("POST", "/announcements", A, {"title": f"{TPREFIX} TB HetHan", "content": "het han",
                                                 "starts_at": "2020-01-01T00:00:00", "ends_at": "2020-02-01T00:00:00"}), 201)
    n_exp = r.data["id"]
    ok("ends_at duoc luu & tra ve dung", str(r.data.get("ends_at", "")).startswith("2020-02-01"))

    expect("soldier POST /announcements -> 403",
           req("POST", "/announcements", S, {"title": f"{TPREFIX} x", "content": "x"}), 403)

    # --- cong khai / khach ---
    r = expect("GUEST GET /announcements", req("GET", "/announcements"), 200)
    g = titles(r.data)
    ok("guest chi thay thong bao is_public", f"{TPREFIX} TB CongKhai" in g and f"{TPREFIX} TB Ghim" not in g)
    expect("GUEST GET /announcements/{noi bo} -> 404", req("GET", f"/announcements/{n_pin}"), 404)
    expect("GUEST GET /announcements/{is_public} -> 200", req("GET", f"/announcements/{n_pub}"), 200)

    # --- ghim / uu tien ---
    r = expect("officer GET /announcements?pinned_only=true", req("GET", "/announcements?pinned_only=true", A), 200)
    g = titles(r.data)
    ok("pinned_only chi tra thong bao ghim", f"{TPREFIX} TB Ghim" in g and f"{TPREFIX} TB CongKhai" not in g)
    r = expect("officer GET /announcements?priority=khan", req("GET", "/announcements?priority=khan&limit=200", A), 200)
    g = titles(r.data)
    ok("loc priority=khan dung", f"{TPREFIX} TB Khan" in g and f"{TPREFIX} TB Ghim" not in g)

    r = expect("officer GET /announcements (mac dinh) - kiem tra thu tu ghim>uu tien", req("GET", "/announcements?limit=200", A), 200)
    ids = [x["id"] for x in r.data]
    ok("thong bao ghim dung truoc thong bao 'khan' khong ghim",
       n_pin in ids and n_khan in ids and ids.index(n_pin) < ids.index(n_khan))

    # --- sua / xoa + rule so huu ---
    expect("officer2 PUT /announcements/{id} cua officer1 -> 403",
           req("PUT", f"/announcements/{n_pub}", B, {"title": f"{TPREFIX} TB CongKhai", "content": "x", "is_public": True}), 403)
    r = expect("officer1 PUT /announcements/{id} cua minh -> 200",
               req("PUT", f"/announcements/{n_pub}", A, {"title": f"{TPREFIX} TB CongKhai (sua)", "content": "da sua", "is_public": True}), 200)
    ok("PUT cap nhat title", r.data["title"] == f"{TPREFIX} TB CongKhai (sua)")
    expect("officer2 DELETE /announcements/{id} cua officer1 -> 403", req("DELETE", f"/announcements/{n_pub}", B), 403)
    expect("officer1 DELETE /announcements/{id} -> 204", req("DELETE", f"/announcements/{n_pub}", A), 204)
    expect("commander DELETE /announcements/{ghim} -> 204", req("DELETE", f"/announcements/{n_pin}", C), 204)
    expect("commander DELETE /announcements/{khan} -> 204", req("DELETE", f"/announcements/{n_khan}", C), 204)
    expect("commander DELETE /announcements/{het han} -> 204", req("DELETE", f"/announcements/{n_exp}", C), 204)
    expect("GET /announcements/{id} sau xoa -> 404", req("GET", f"/announcements/{n_pin}", C), 404)

    # ============================================================== MODULE 3
    head("MODULE 3 - DOCUMENTS: quyen quan ly (chi role 0-2), phan quyen xem theo bac, tai ve")

    # Quan ly Van ban - Tai lieu - Bieu mau: CHI Quan tri (0) / Lu truong-Chinh uy (1)
    # / Lu pho-Pho chinh uy (2) - xem app/core/roles.py DOCUMENT_MANAGE_ROLES.
    # Ca nhan (role 4) va Nguoi dung (role 5) chi duoc XEM / TAI VE. Module documents
    # KHONG ap rule so huu ("chi tac gia") - moi tai khoan role 0-2 deu sua/xoa duoc.
    expect("officer (role 4) POST /documents -> 403",
           req("POST", "/documents", A, multipart=({"title": f"{TPREFIX} x", "category": "bao_cao"}, [("file", *PDF)])), 403)
    expect("soldier (role 5) POST /documents -> 403",
           req("POST", "/documents", S, multipart=({"title": f"{TPREFIX} x", "category": "bao_cao"}, [("file", *PDF)])), 403)

    r = expect("commander POST /documents (noi_bo, PDF) -> 201",
               req("POST", "/documents", C, multipart=(
                   {"title": f"{TPREFIX} Tai lieu NoiBo", "category": "bao_cao", "description": "mo ta"},
                   [("file", *PDF)])), 201)
    d_nb = r.data["id"]
    ok("file_url = /static/documents/...", str(r.data["file_url"]).startswith("/static/documents/"))
    ok("file_name giu ten goc", r.data["file_name"] == "bao_cao.pdf")
    ok("file_size > 0", r.data["file_size"] > 0)
    ok("classification mac dinh = noi_bo", r.data["classification"] == "noi_bo")

    r = expect("commander POST /documents (cong_khai, PDF) -> 201",
               req("POST", "/documents", C, multipart=(
                   {"title": f"{TPREFIX} Tai lieu CongKhai", "category": "huong_dan", "classification": "cong_khai"},
                   [("file", *PDF)])), 201)
    d_ck = r.data["id"]

    r = expect("commander POST /documents (mat) -> 201 (chi huy co san quyen MAT)",
               req("POST", "/documents", C, multipart=(
                   {"title": f"{TPREFIX} Tai lieu MAT", "category": "van_ban_chi_dao", "classification": "mat"},
                   [("file", *PDF)])), 201)
    d_mat = r.data["id"]

    # --- phan quyen xem (loc theo classification, doc lap voi quyen quan ly) ---
    r = expect("GUEST GET /documents", req("GET", "/documents"), 200)
    g = titles(r.data)
    ok("guest chi thay tai lieu cong_khai",
       f"{TPREFIX} Tai lieu CongKhai" in g and f"{TPREFIX} Tai lieu NoiBo" not in g and f"{TPREFIX} Tai lieu MAT" not in g)
    r = expect("SOLDIER GET /documents", req("GET", "/documents", S), 200)
    s = titles(r.data)
    ok("soldier thay cong_khai + noi_bo, khong thay MAT",
       f"{TPREFIX} Tai lieu CongKhai" in s and f"{TPREFIX} Tai lieu NoiBo" in s and f"{TPREFIX} Tai lieu MAT" not in s)
    expect("SOLDIER GET /documents/{mat} -> 404", req("GET", f"/documents/{d_mat}", S), 404)
    r = expect("clearance officer GET /documents (thay ca MAT)", req("GET", "/documents", L), 200)
    ok("clearance officer thay tai lieu MAT", f"{TPREFIX} Tai lieu MAT" in titles(r.data))

    # --- tai ve ---
    expect("GUEST GET /documents/{cong_khai}/download -> 200", req("GET", f"/documents/{d_ck}/download"), 200)
    expect("GUEST GET /documents/{noi_bo}/download -> 404", req("GET", f"/documents/{d_nb}/download"), 404)
    expect("SOLDIER GET /documents/{noi_bo}/download -> 200", req("GET", f"/documents/{d_nb}/download", S), 200)
    expect("clearance officer GET /documents/{mat}/download -> 200", req("GET", f"/documents/{d_mat}/download", L), 200)
    expect("SOLDIER GET /documents/{mat}/download -> 404", req("GET", f"/documents/{d_mat}/download", S), 404)

    # --- sua meta / xoa: chi role 0-2 ---
    expect("officer PUT /documents/{id} -> 403",
           req("PUT", f"/documents/{d_nb}", A, multipart=({"title": f"{TPREFIX} x", "category": "bao_cao"}, [])), 403)
    r = expect("commander PUT /documents/{id} (sua meta) -> 200",
               req("PUT", f"/documents/{d_nb}", C, multipart=(
                   {"title": f"{TPREFIX} Tai lieu NoiBo (sua)", "category": "ke_hoach", "description": "cap nhat"}, [])), 200)
    ok("PUT cap nhat title + category", r.data["title"] == f"{TPREFIX} Tai lieu NoiBo (sua)" and r.data["category"] == "ke_hoach")
    expect("officer DELETE /documents/{id} -> 403", req("DELETE", f"/documents/{d_nb}", A), 403)
    expect("commander DELETE /documents/{noi_bo} -> 204", req("DELETE", f"/documents/{d_nb}", C), 204)
    expect("GET /documents/{id} sau xoa -> 404", req("GET", f"/documents/{d_nb}", C), 404)
    expect("commander DELETE /documents/{cong_khai} -> 204", req("DELETE", f"/documents/{d_ck}", C), 204)
    expect("commander DELETE /documents/{mat} -> 204", req("DELETE", f"/documents/{d_mat}", C), 204)

    # ============================================================== MODULE 4
    head("MODULE 4 - EDUCATION MATERIALS: yeu cau dang nhap, tao, period_label, dinh kem, xoa")

    expect("GUEST GET /education-materials -> 401 (bat buoc JWT)", req("GET", "/education-materials"), 401, 403)

    r = expect("officer POST /education-materials -> 201",
               req("POST", "/education-materials", A, {
                   "title": f"{TPREFIX} GDCT Tuyen truyen", "category": "tuyen_truyen",
                   "period_label": "Tuan 35/2026", "content": "noi dung gdct",
                   "attachment_url": "/static/edu/demo.pdf"}), 201)
    e1 = r.data["id"]
    ok("period_label + attachment_url tra ve dung",
       r.data["period_label"] == "Tuan 35/2026" and r.data["attachment_url"] == "/static/edu/demo.pdf")

    r = expect("commander POST /education-materials -> 201",
               req("POST", "/education-materials", C, {
                   "title": f"{TPREFIX} GDCT Phap luat", "category": "phap_luat_bien_gioi", "content": "phap luat bien gioi"}), 201)
    e2 = r.data["id"]

    expect("soldier POST /education-materials -> 403",
           req("POST", "/education-materials", S, {"title": f"{TPREFIX} x", "category": "tuyen_truyen", "content": "x"}), 403)

    r = expect("SOLDIER GET /education-materials -> 200 (moi tai khoan da kich hoat)", req("GET", "/education-materials?limit=200", S), 200)
    s = titles(r.data)
    ok("soldier doc duoc danh sach GDCT", f"{TPREFIX} GDCT Tuyen truyen" in s)
    expect("SOLDIER GET /education-materials/{id} -> 200", req("GET", f"/education-materials/{e1}", S), 200)

    r = expect("GET /education-materials?category=tuyen_truyen", req("GET", "/education-materials?category=tuyen_truyen&limit=200", A), 200)
    g = titles(r.data)
    ok("loc category dung", f"{TPREFIX} GDCT Tuyen truyen" in g and f"{TPREFIX} GDCT Phap luat" not in g)

    r = expect("officer1 PUT /education-materials/{id} cua minh -> 200",
               req("PUT", f"/education-materials/{e1}", A, {
                   "title": f"{TPREFIX} GDCT Tuyen truyen (sua)", "category": "tuyen_truyen", "content": "da sua"}), 200)
    ok("PUT cap nhat title", r.data["title"] == f"{TPREFIX} GDCT Tuyen truyen (sua)")
    expect("officer2 PUT /education-materials/{id} cua officer1 -> 403",
           req("PUT", f"/education-materials/{e1}", B, {"title": f"{TPREFIX} x", "category": "tuyen_truyen", "content": "x"}), 403)
    expect("officer2 DELETE /education-materials/{id} cua officer1 -> 403", req("DELETE", f"/education-materials/{e1}", B), 403)
    expect("officer1 DELETE /education-materials/{id} -> 204", req("DELETE", f"/education-materials/{e1}", A), 204)
    expect("GET /education-materials/{id} sau xoa -> 404", req("GET", f"/education-materials/{e1}", S), 404)
    expect("commander DELETE /education-materials/{id} cua officer khac -> 204", req("DELETE", f"/education-materials/{e2}", C), 204)

    # ============================================================== MODULE 5
    head("MODULE 5 - HOME: /home/public (khach) + /home/summary (da dang nhap)")

    # Du lieu rieng cho trang chu (commander tao -> post tu da_duyet).
    r = expect("commander POST /posts (home, cong_khai, featured)",
               req("POST", "/posts", C, {"title": f"{TPREFIX} Home Post", "category": "huan_luyen",
                                         "content": "home", "classification": "cong_khai", "is_featured": True}), 201)
    h_post = r.data["id"]
    r = expect("commander POST /announcements (home, is_public)",
               req("POST", "/announcements", C, {"title": f"{TPREFIX} Home TB", "content": "home tb", "is_public": True}), 201)
    h_ann = r.data["id"]
    r = expect("commander POST /documents (home, cong_khai)",
               req("POST", "/documents", C, multipart=(
                   {"title": f"{TPREFIX} Home Doc", "category": "huong_dan", "classification": "cong_khai"}, [("file", *PDF)])), 201)
    h_doc = r.data["id"]
    r = expect("commander POST /education-materials (home)",
               req("POST", "/education-materials", C, {
                   "title": f"{TPREFIX} Home GDCT", "category": "tuyen_truyen", "content": "home gdct"}), 201)
    h_edu = r.data["id"]

    # --- /home/public (khong JWT) ---
    r = expect("GUEST GET /home/public -> 200", req("GET", "/home/public?limit=20"), 200)
    keys_ok = all(k in r.data for k in ("featured_posts", "public_announcements", "public_documents"))
    ok("/home/public co du 3 nhom du lieu", keys_ok)
    if keys_ok:
        show("home/public", {k: len(r.data[k]) for k in ("featured_posts", "public_announcements", "public_documents")})
        ok("featured_posts chua bai cong_khai featured", any(x["title"] == f"{TPREFIX} Home Post" for x in r.data["featured_posts"]))
        ok("public_announcements chua thong bao is_public", any(x["title"] == f"{TPREFIX} Home TB" for x in r.data["public_announcements"]))
        ok("public_documents chua tai lieu cong_khai", any(x["title"] == f"{TPREFIX} Home Doc" for x in r.data["public_documents"]))

    # --- /home/summary (bat buoc JWT) ---
    expect("GUEST GET /home/summary -> 401", req("GET", "/home/summary"), 401, 403)
    r = expect("SOLDIER GET /home/summary -> 200", req("GET", "/home/summary?limit=20", S), 200)
    keys_ok = all(k in r.data for k in ("latest_posts", "latest_education_materials", "latest_directives", "latest_announcements"))
    ok("/home/summary co du 4 nhom du lieu", keys_ok)
    if keys_ok:
        show("home/summary", {k: len(r.data[k]) for k in ("latest_posts", "latest_education_materials", "latest_directives", "latest_announcements")})
        ok("latest_posts chi gom bai da_duyet", all(p["status"] == "da_duyet" for p in r.data["latest_posts"]))
        ok("latest_posts chua bai home", any(x["title"] == f"{TPREFIX} Home Post" for x in r.data["latest_posts"]))
        ok("latest_announcements chua thong bao home", any(x["title"] == f"{TPREFIX} Home TB" for x in r.data["latest_announcements"]))
        ok("latest_education_materials chua GDCT home", any(x["title"] == f"{TPREFIX} Home GDCT" for x in r.data["latest_education_materials"]))
    expect("COMMANDER GET /home/summary -> 200", req("GET", "/home/summary", C), 200)

    # --- don du lieu trang chu ---
    expect("commander DELETE home post", req("DELETE", f"/posts/{h_post}", C), 204)
    expect("commander DELETE home announcement", req("DELETE", f"/announcements/{h_ann}", C), 204)
    expect("commander DELETE home document", req("DELETE", f"/documents/{h_doc}", C), 204)
    expect("commander DELETE home education material", req("DELETE", f"/education-materials/{h_edu}", C), 204)


if __name__ == "__main__":
    print("KIEM THU E2E CAC MODULE NOI DUNG  |  tag =", TAG)
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
