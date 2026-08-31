---
name: contract-first-handshake
description: Quy trình 5 bước bắt tay bàn giao Contract-First giữa Backend và Frontend cho dự án Cổng thông tin Lữ đoàn Thông tin 21. Bắt buộc áp dụng sau khi thêm/sửa bất kỳ endpoint nào, trước khi chuyển sang code Frontend.
version: 1.0.0
license: MIT
metadata:
  author: AI-Developer-Assistant
  pairs-with: fast-api-mysql-auto-schema
---

# SKILL: Contract-First Handshake (Bắt tay bàn giao Contract-First)

## Mục tiêu
`openapi.yaml` ở thư mục gốc là **hợp đồng API duy nhất** giữa Backend và Frontend.
Mọi thay đổi endpoint/schema ở Backend chỉ được coi là "hoàn thành" khi hợp đồng đã
được xuất lại, biên bản bàn giao đã ghi vào `openapi.CHANGELOG.md`, và Frontend đã
có đủ thông tin để đồng bộ TypeScript types. Skill này định nghĩa 5 bước bắt buộc,
theo thứ tự, không được bỏ bước.

Skill này đi kèm `fast-api-mysql-auto-schema` (đọc cả hai trước khi làm việc với
database/CRUD): skill kia lo phần *sinh code 3 tầng*, skill này lo phần *bàn giao hợp đồng*.

---

## Bước 1 — Backend viết chuẩn 3 tầng + RBAC + phân loại

- Viết đủ 3 tầng, không nhồi logic/query vào route:
  1. `app/repositories/<entity>_repository.py` — hàm thuần truy vấn DB
     (`create`, `list_all`, `get`, `update`, `delete`), nhận `db: Session`,
     **không** import `HTTPException`.
  2. `app/services/<entity>_service.py` — nghiệp vụ: gọi repository, raise
     `HTTPException` (400/403/404/409...), áp rule sở hữu
     ("chỉ tác giả hoặc `commander`"), tự join `author_full_name`.
  3. `app/api/routes/<entity>s.py` — chỉ khai báo path/method/status/`Depends`,
     gọi đúng 1 hàm service rồi trả kết quả. Không chứa `if`/query DB.
- Model kế thừa `Base`, có `author_id` (FK `users.id`) + `created_at` nếu là
  nội dung do người dùng đăng.
- **RBAC** (theo `app/api/deps.py`): `get_current_user` / `get_optional_user` /
  `require_roles(*roles)` / `bootstrap_or_role(*roles)`. Áp ở mức router khi
  toàn bộ endpoint cùng quyền; áp ở mức route khi chỉ vài method cần quyền riêng.
  Map role: `commander` = Ban chỉ huy, `officer` = Cán bộ/Nhân viên,
  `soldier` = nội bộ chỉ xem.
- **3 bậc phân loại** (`classification` trên `posts`, `directives`, `documents`):
  `cong_khai` (khách LAN xem được) · `noi_bo` (mọi tài khoản đã kích hoạt) ·
  `mat` (chỉ `commander` HOẶC `User.clearance = True`).
  - Lọc danh sách ở **service** qua `allowed_classifications(current_user)`.
  - Kiểm tra 1 item qua `can_view_classification(item.classification, user)`
    → trả **404** nếu không được xem (không lộ tồn tại).
  - Tạo/sửa nội dung bậc `mat` yêu cầu `has_secret_clearance(current_user)` → 403 nếu thiếu.
  - Helper ở `app/core/access.py`.
- Đăng ký router mới trong `app/main.py` bằng `app.include_router(...)`,
  **không** xoá/ghi đè router cũ. Nếu hợp đồng đổi, tăng `API_VERSION` trong `app/main.py`.

**Đầu ra Bước 1:** code 3 tầng + router đã include, mã HTTP đúng chuẩn
(200/201/204/400/403/404/409/422).

---

## Bước 2 — Kiểm thử logic, schema và runtime API

Chạy trong môi trường backend (`backend/venv/Scripts/python.exe`), từ thư mục `backend/`:

1. **Import & schema:** `python -c "from app.main import app; print(len(app.routes))"`
   — không lỗi import; `Base.metadata.create_all` chạy sạch; nếu là bảng cũ cần
   thêm cột thì chạy script migration tương ứng trong `scripts/` (idempotent).
2. **Logic:** kiểm tra rule sở hữu, RBAC, lọc phân loại, các nhánh raise
   `HTTPException` (403/404/409). Ưu tiên test tự động nếu dự án đã có; nếu chưa,
   test tay bằng script ngắn gọi thẳng service.
3. **Runtime API:** khởi chạy `uvicorn app.main:app --port 8000` rồi `curl` (hoặc
   `/docs`) các endpoint vừa thêm — xác nhận status code, hình dạng JSON,
   phân biệt khách/đã đăng nhập đúng như thiết kế.

**Đầu ra Bước 2:** báo cáo ngắn: endpoint nào đã test, status trả về, điểm cần lưu ý.
Nếu có lỗi → báo lỗi gốc từ MySQL/SQLAlchemy/FastAPI, **không** nuốt lỗi, quay lại Bước 1.

---

## Bước 3 — Xuất lại hợp đồng `openapi.yaml`

Bắt buộc chạy (từ thư mục `backend/`):

```
venv/Scripts/python.exe scripts/export_openapi.py
```

- Script import trực tiếp `app` và gọi `app.openapi()` — **không cần** server đang chạy.
- Ghi đè `openapi.yaml` ở thư mục gốc, kèm header: phiên bản API + thời điểm sinh +
  số path/operation.
- **Không** sửa tay `openapi.yaml`. Nếu số path/operation không đổi mà đáng lẽ phải
  đổi → xem lại Bước 1 (router chưa include? quên tăng `API_VERSION`?).

**Đầu ra Bước 3:** dòng log `Da xuat phien ban X.Y.Z: N path / M operation` +
xác nhận `openapi.yaml` đã thay đổi.

---

## Bước 4 — Ghi biên bản bàn giao vào `openapi.CHANGELOG.md`

Thêm **một mục mới lên đầu** phần lịch sử của `openapi.CHANGELOG.md` (thư mục gốc),
theo mẫu:

```markdown
## vX.Y.Z — YYYY-MM-DD

**Người bàn giao:** Backend
**Phạm vi:** <module/entity liên quan>

### Thêm / Sửa / Xoá endpoint
- `POST /xxx` — mô tả ngắn, quyền yêu cầu, phân loại áp dụng
- `GET /xxx/{id}` — ...

### Thay đổi schema
- `XxxOut`: thêm trường `foo: bool`, ...

### Ảnh hưởng Frontend
- Cần cập nhật `frontend/src/types/xxx.ts`
- Màn hình/route bị ảnh hưởng: ...

### Kiểm thử đã thực hiện
- <tóm tắt kết quả Bước 2>
```

- `X.Y.Z` phải khớp `API_VERSION` trong `app/main.py` và header `openapi.yaml`.
- Nếu `openapi.CHANGELOG.md` chưa tồn tại → tạo mới với tiêu đề và mục v1.3.0 làm mốc.
- Quy ước tăng phiên bản: sửa/thêm không phá vỡ → tăng **MINOR**;
  đổi/xoá field, đổi kiểu, đổi mã lỗi → tăng **MAJOR**; chỉ sửa mô tả → **PATCH**.

**Đầu ra Bước 4:** mục changelog mới đã ghi, phiên bản đồng nhất 3 nơi
(`app/main.py`, `openapi.yaml`, `openapi.CHANGELOG.md`).

---

## Bước 5 — Bàn giao sang Frontend

Chỉ được bắt đầu code Frontend **sau khi** Bước 3 và Bước 4 xong.

1. **Đồng bộ TypeScript types** trong `frontend/src/types/`:
   - Mỗi schema trong `openapi.yaml` (`XxxCreate`, `XxxOut`, enum phân loại/trạng thái)
     ↔ một interface/type trong `frontend/src/types/<entity>.ts`.
   - Tên trường, kiểu, `optional` (`?`) phải khớp `openapi.yaml` — nguồn sự thật là
     hợp đồng, không phải trí nhớ.
   - Enum dùng union type literal (`'cong_khai' | 'noi_bo' | 'mat'`), khớp giá trị backend.
2. **Tầng gọi API** trong `frontend/src/api/`:
   - Dùng `API_BASE_URL` từ `import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'`.
   - Gắn `Authorization: Bearer <token>` khi endpoint cần JWT; endpoint công khai thì không.
   - Trả về đúng type đã khai ở `frontend/src/types/`.
3. **Dựng UI kết nối API:**
   - Ẩn/hiện nút theo `role` / `hasClearance` đọc từ `AuthContext` — chỉ là UX,
     **không** thay cho enforce ở backend.
   - Xử lý các mã lỗi hợp đồng: 401 (hết hạn → đăng nhập lại), 403 (không đủ quyền),
     404 (không tồn tại / không được xem), 409 (xung đột), 422 (sai input).
4. **Đối chiếu cuối:** mở `openapi.yaml`, rà từng endpoint mới → đã có type, có hàm
   gọi API, có chỗ dùng trên UI (hoặc ghi chú lý do chưa dùng).

**Đầu ra Bước 5:** danh sách file `frontend/src/types/*` và `frontend/src/api/*`
đã thêm/sửa, màn hình đã kết nối, cùng ghi chú phần còn tồn đọng (nếu có).

---

## Checklist bàn giao (dán vào báo cáo hoàn thành)

- [ ] B1: 3 tầng đủ, router đã `include_router`, RBAC + phân loại áp đúng
- [ ] B2: import OK, logic + runtime API đã test, mã HTTP đúng chuẩn
- [ ] B3: đã chạy `scripts/export_openapi.py`, `openapi.yaml` cập nhật
- [ ] B4: `openapi.CHANGELOG.md` có mục mới, phiên bản khớp 3 nơi
- [ ] B5: `frontend/src/types/` + `frontend/src/api/` đồng bộ, UI đã nối, đã đối chiếu hợp đồng
