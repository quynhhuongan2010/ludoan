# Biên bản bàn giao hợp đồng API — cho Frontend

> File này để FE biết **bản hợp đồng mới nhất** đang là bản nào và có gì thay đổi.
> Nguồn sự thật đầy đủ: `openapi.yaml` (thư mục này, sao y bản gốc `d:/Du_an_Lu_doan/ludoan-main/openapi.yaml`)
> Lịch sử chi tiết: `openapi.CHANGELOG.md` (cùng thư mục này) hoặc `../../openapi.CHANGELOG.md`

---

## ✅ BẢN MỚI NHẤT ĐANG HIỆU LỰC: **v4.0.0** — 2026-09-02

- **File**: `frontend/docs-backend/openapi.yaml` (**82 path / 125 operation**, sinh từ backend — KHÔNG sửa tay).
- **Bàn giao bởi**: Backend.
- **Phạm vi**: **Lịch trực – Kíp trực** — làm lại module thành *quy trình phê duyệt lịch trực tuần theo từng đơn vị*.
- **⚠️ BREAKING (MAJOR)**: xoá `POST /duty-schedules`; đổi ngữ nghĩa `PUT` / `DELETE /duty-schedules/{id}`.

### Có gì mới so với v3.1.0

| Nhóm | Chi tiết |
|---|---|
| ➕ Thực thể | `duty_week_plans` (bảng trực tuần 1 đơn vị / 1 tuần, `status`: `nhap`/`cho_duyet`/`da_duyet`/`tra_lai`, UNIQUE `unit_id + week_start`). |
| ➕ Cột trên `duty_schedules` | `week_plan_id`, `unit_id`, `unit_name`, `duty_type`, `duty_type_label`, `contact_phone`, `personnel_present`, `personnel_total`. |
| ➕ Enum | `DutyType` (7 cương vị): `truc_chi_huy`, `truc_ban_tac_chien`, `truc_ban_noi_vu`, `truc_chuyen_mon`, `truc_ca_kip`, `truc_bao_ve`, `khac`. |
| ➕ Endpoint `/duty-week-plans` | `POST` · `GET` (`?unit_id=&week_of=&status_filter=`) · `GET /{id}` · `PUT /{id}` (sửa `note`) · `DELETE /{id}` · `POST /{id}/entries` (thêm dòng ca trực) · `POST /{id}/submit` · `POST /{id}/review` (**chỉ `commander`/`admin`**, `{status, review_note?}`) · `POST /{id}/reopen`. |
| ➕ Bảng tổng hợp | `GET /duty-schedules/board/day?day=YYYY-MM-DD[&unit_id=]` → `DutyDayBoard` (gom theo đơn vị + quân số). `GET /duty-schedules/board/week?week_of=YYYY-MM-DD[&unit_id=]` → `DutyWeekBoard` (7 ngày + `unit_plans`). |
| 🔴 Xoá | `POST /duty-schedules` → nay tạo ca trực qua `POST /duty-week-plans/{id}/entries`. |
| 🔄 Đổi nghĩa | `PUT` / `DELETE /duty-schedules/{id}` = sửa/xoá **một dòng ca trực trong bảng trực tuần** (dòng cũ không gắn bảng → **409**; sai đơn vị → **403**; bảng đã trình/duyệt → **409**). `GET /duty-schedules/{id}` thêm ràng buộc quyền xem (ngoài phạm vi → **404**). |
| 🔄 Mở rộng | `GET /duty-schedules` thêm query `unit_id?`, `duty_type?`; kết quả lọc theo quyền; mỗi phần tử thêm các field cột mới ở trên. |

**Luồng phê duyệt** (giống `posts`): đơn vị lập bảng `nhap` → thêm dòng ca trực →
`submit` → `cho_duyet` → chỉ huy Lữ đoàn `review` (`da_duyet` / `tra_lai`) → nếu cần
`reopen` về `nhap`. Dòng ca trực chỉ thêm/sửa/xoá khi bảng cha ở `nhap`/`tra_lai`.

**Phân quyền tóm tắt:**
- Router `/duty-week-plans` yêu cầu JWT. `POST` cần `officer`/`commander`; `officer` bị
  ép `unit_id = User.unit_id` (chưa gán đơn vị → **400**); `commander`/`admin` chọn đơn vị bất kỳ.
- `review` **chỉ `commander`/`admin`**. `reopen` bảng `da_duyet` cũng chỉ `commander`/`admin`.
- `officer` xem bảng đơn vị mình (mọi trạng thái) + bảng `da_duyet` của đơn vị khác.

### FE cần cập nhật cho v4.0.0

- `frontend/src/types/dutySchedule.ts`: thêm `DutyType` + `DUTY_TYPE_LABELS`,
  `DutyPlanStatus` + labels, field mới trên `DutySchedule`, `DutyDayBoard`,
  `DutyWeekBoard`, `DutyWeekPlan`, `DutyWeekPlanDetail`, `DutyWeekPlanBrief`,
  `DutyWeekPlanCreate`, `DutyWeekPlanReview`.
- `frontend/src/api/dutySchedules.ts`: **bỏ `create`**; đổi `update`/`remove` thành
  thao tác trên một dòng; thêm `dayBoard`, `weekBoard`; thêm `dutyWeekPlansApi`
  (`list`/`get`/`create`/`update`/`remove`/`addEntry`/`submit`/`review`/`reopen`).
- Màn hình mới `frontend/src/pages/DutyRosterPage.tsx` route `/lich-truc` (3 tab:
  Kíp trực theo ngày · Trực tuần · Bảng trực đơn vị). Gỡ khối "Lịch trực kíp" khỏi
  `AnnouncementsPage.tsx`; thêm mục NAV; thêm `Route` trong `App.tsx`.
- Migration DB (nếu DB cũ đã có `duty_schedules`): chạy một lần
  `venv/Scripts/python.exe scripts/migrate_duty_schedule_unit.py` (idempotent).

---

## Bản trước — v3.1.0 (2026-09-02): `POST /api/upload`

Vẫn còn hiệu lực (không bị v4.0.0 đụng tới).

- `POST /api/upload` — `multipart/form-data`, field `file`. Quyền: JWT role `officer`
  hoặc `commander`/`admin`. Định dạng: ảnh `.jpg .jpeg .png .webp .gif` + tài liệu
  `.pdf .doc .docx .xls .xlsx .ppt .pptx`. Sai định dạng / vượt `MAX_UPLOAD_MB` (25) /
  file rỗng → **400**; thiếu JWT → **401**; role không đủ → **403**. Thành công →
  **201** + `UploadOut` = `{ status: "success", filename: string, url: string }`.
  File đổi tên `<uuid>.<ext>`, phục vụ qua `url` = `/static/common/<uuid>.<ext>`.
- **[Bổ sung sau — không đổi hợp đồng OpenAPI]** endpoint nay nhận thêm **video**
  `.mp4 .webm .ogg .mov .m4v` (chèn video giữa bài Tin tức / Giáo dục chính trị).
  Video có giới hạn dung lượng riêng, lớn hơn: `MAX_VIDEO_UPLOAD_MB` (mặc định **200**);
  ảnh + tài liệu vẫn theo `MAX_UPLOAD_MB` (25). Danh sách định dạng là kiểm tra runtime,
  không nằm trong schema → `openapi.yaml` không đổi.
- FE đã đồng bộ: `frontend/src/types/upload.ts`, `frontend/src/api/uploads.ts`
  (`uploadsApi.upload(file: File): Promise<UploadOut>`, tự gắn `Authorization: Bearer`).
- **[Cập nhật 2026-09-02, sau bản này — không đổi hợp đồng API]** Đã gắn vào UI thật:
  - `frontend/src/pages/EducationFormPage.tsx` — trường "Tài liệu đính kèm" (Giáo dục
    chính trị): chọn file (.jpg/.jpeg/.png/.pdf/.doc/.docx, ≤ 20MB) → `uploadsApi.upload()`
    → gán `url` vào `attachment_url` trước khi submit (JSON).
  - `frontend/src/components/RichContentEditor.tsx` (mới) — ô soạn `contentEditable`
    dùng chung cho **Tin tức** (`PostsPage.tsx`) và **Giáo dục chính trị**: dán ảnh
    (Ctrl+V), kéo-thả, hoặc "Chèn ảnh" → `uploadsApi.upload()` → chèn `<img>` tại con
    trỏ. Ảnh lưu là thẻ `<img src="/static/common/...">` ngay trong `content` gửi lên
    `POST/PUT /posts` và `POST/PUT /education-materials` — **không schema/endpoint nào đổi**.
  - `frontend/src/components/RichContent.tsx` (mới) — render lại `content` (lọc XSS
    bằng `dompurify`, thêm tiền tố origin API cho ảnh `/static/...`).
  - Thư viện mới: `dompurify` (+ `@types/dompurify`) — chỉ phía FE, không ảnh hưởng hợp đồng.

---

## ⚠️ Lưu ý xung đột số phiên bản

Trong thư mục này còn file **`openapi.draft-content-access.yaml`** (trước đây từng là `openapi.yaml`):

- Đó là **bản nháp FE viết tay** đề xuất tính năng *"Hạn chế quyền đăng bài + kiểm duyệt"*
  (`content_publish_access`, `content_review_access`, `PATCH /users/{user_id}/content-access`,
  sửa quyền `POST /posts/{id}/review`).
- Bản nháp đó ghi là `3.1.0-draft` nhưng **CHƯA được cài đặt ở backend**.
- Các số `3.1.0` và `4.0.0` đã bị dùng cho tính năng khác. Việc đánh số lại cho
  "hạn chế quyền đăng bài" do người điều phối dự án quyết (dự kiến `4.1.0` trở đi).
- Giữ file này để không mất nội dung đề xuất; **không dùng nó làm hợp đồng thi công.**

---

## Bảng theo dõi các bản đã bàn giao

| Phiên bản | Ngày | Phạm vi | Trạng thái |
|---|---|---|---|
| **v4.0.0** | 2026-09-02 | Lịch trực – Kíp trực: quy trình phê duyệt lịch trực tuần theo đơn vị (BREAKING) | ✅ Hiệu lực (`openapi.yaml` — 82 path / 125 op) |
| v3.1.0 | 2026-09-02 | `POST /api/upload` — upload file dùng chung | ✅ Hiệu lực (không bị v4.0.0 đụng) |
| v3.0.0 | 2026-09-01 | Bỏ vai trò `soldier`; bắt buộc rank/position/unit khi tạo/kích hoạt user | ✅ (xem CHANGELOG) |
| 3.1.0-draft (content-access) | — | Đề xuất "Hạn chế quyền đăng bài + kiểm duyệt" | ❌ Chưa code — `openapi.draft-content-access.yaml` |
