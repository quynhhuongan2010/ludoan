# Lịch sử hợp đồng API — Cổng thông tin Lữ đoàn Thông tin 21

File này là **biên bản bàn giao Contract-First** giữa Backend và Frontend.
Nguồn sự thật của hợp đồng là `openapi.yaml` (sinh tự động từ backend bằng
`backend/scripts/export_openapi.py` — KHÔNG sửa tay). Mỗi lần thêm/sửa/xoá
endpoint hoặc schema, ghi một mục mới lên **đầu** phần "Lịch sử thay đổi" theo
đúng quy trình `.claude/skills/contract-first-handshake/SKILL.md` (Bước 4).

Quy ước phiên bản (phải khớp `API_VERSION` trong `backend/app/main.py`,
header `openapi.yaml`, và mục changelog tương ứng):

| Loại thay đổi | Tăng |
|---|---|
| Thêm endpoint/field mới, không phá vỡ client cũ | MINOR (x.**Y**.z) |
| Đổi tên/kiểu/optional của field, xoá endpoint, đổi mã lỗi | MAJOR (**X**.y.z) |
| Chỉ sửa mô tả/tài liệu, không đổi hình dạng dữ liệu | PATCH (x.y.**Z**) |

---

## Lịch sử thay đổi

## v1.9.1 — 2026-08-30

**Người bàn giao:** Backend
**Phạm vi:** Đóng gói vận hành sản xuất (Production) — phục vụ Frontend tĩnh qua cùng 1 cổng.
**Quy mô:** 62 path / 100 operation (không thêm/xoá endpoint, không đổi field).

### Sửa endpoint
- `GET /` — **hành vi có điều kiện**, không đổi hình dạng response (schema vẫn `{}` như cũ):
  - Nếu đã có bản build tĩnh Frontend tại `frontend/dist` (đã chạy `npm run build`): trả về
    `index.html` (SPA) thay vì JSON thông tin API.
  - Nếu chưa build Frontend (chế độ API-only lúc phát triển): **giữ nguyên** JSON cũ
    `{name, status, docs, openapi}` như trước — không phá vỡ client cũ.
- **Mới (không phải endpoint nghiệp vụ, không xuất hiện trong OpenAPI —** `include_in_schema=False`
  **):** route catch-all `GET /{full_path:path}` + mount tĩnh `/assets` — phục vụ các file build của
  Frontend (`frontend/dist`) và trả `index.html` cho mọi đường dẫn điều hướng phía client (React
  Router) không khớp router API nào. Đăng ký **sau cùng** (sau mọi `app.include_router`) nên không
  che bất kỳ endpoint API thật nào — đã kiểm chứng: `GET /docs`, `/openapi.json`, `/static/...`,
  `/items` (401 do chưa đăng nhập, không phải SPA) vẫn đúng như cũ.
  - **Giới hạn đã biết:** trang `/items` (demo CRUD nội bộ, không thuộc sitemap nghiệp vụ ở
    `.claude/CLAUDE.md`) trùng đường dẫn với `GET /items` — F5 trực tiếp trên URL này trả JSON của
    API thay vì giao diện; điều hướng từ trong ứng dụng (SPA, không tải lại trang) vẫn hoạt động
    bình thường.

### Thay đổi schema
- Không.

---

## v1.9.0 — 2026-08-30

**Người bàn giao:** Backend
**Phạm vi:** Tin tức – Hoạt động đơn vị (`posts`) — bộ lọc theo bậc phân loại + rà soát RBAC.
**Quy mô:** 62 path / 100 operation (không thêm/xoá endpoint — chỉ thêm 1 query param).

### Sửa endpoint
- `GET /posts` — **thêm** query param `classification` (`cong_khai` | `noi_bo` | `mat`), tuỳ chọn.
  - Lọc danh sách tin theo đúng bậc phân loại đó, **sau khi** đã giao với danh sách bậc mà
    người gọi được phép xem (`allowed_classifications`): khách chỉ `cong_khai`; tài khoản đã
    kích hoạt thêm `noi_bo`; `commander`/`admin` hoặc `User.clearance=True` thêm `mat`.
  - Xin bậc không được phép xem → trả **danh sách rỗng** (không lộ tồn tại, không 403).
  - Giá trị ngoài 3 bậc hợp lệ → **422** (`Bậc phân loại không hợp lệ...`).
  - Áp cho cả 3 nhánh xem (khách/`soldier`, `officer`, `commander`); `officer` vẫn luôn thấy
    bài của chính mình bất kể bộ lọc (giữ nguyên hành vi cũ).

### Thay đổi schema
- Không. `PostOut` / `PostCreate` giữ nguyên hình dạng.

### RBAC — kết quả rà soát (không thay đổi code, xác nhận đang đúng)
- `POST` / `PUT` / `DELETE /posts` và `/posts/{id}/thumbnail`: `require_roles("officer","commander")`
  (`admin` kế thừa) → `soldier` / khách **403**.
- `POST /posts/{id}/review`: chỉ `commander`/`admin`.
- Tạo/sửa bài `classification=mat` khi thiếu quyền MẬT → **403** (`_guard_secret_content`).
- Luồng duyệt: `officer` đăng → `cho_duyet`; `commander` đăng → `da_duyet`; `officer` sửa bài
  đã duyệt/trả lại → tự về `cho_duyet`.
- Chỉ thị / Giao nhiệm vụ: ban hành + giao + duyệt báo cáo chỉ `commander`/`admin`
  (`_require_commander`); cấp dưới chỉ nộp/xem trong phạm vi `unit_id` / `assignee_id` của mình
  (`_target_belongs_to_user`, `_visible_or_404` → 403/404).

### Ảnh hưởng Frontend
- `frontend/src/api/posts.ts`: `list()` nhận thêm `classification`.
- `frontend/src/types/post.ts`: không đổi (không có field mới ở response).
- Màn hình: `PostsPage.tsx` thêm dropdown lọc “Công khai / Nội bộ / MẬT”.
- `UsersPage.tsx`: chỉ thêm chú thích (không đổi hành vi / API).

### Kiểm thử đã thực hiện
- `python -c "from app.main import app"` — import sạch, `create_all` + bootstrap chạy không lỗi.
- Script `test_post_rbac.py` (SQLite in-memory, 15 assertion) — tất cả PASS: phân biệt
  khách / `soldier` / `soldier`+clearance / `officer` / `commander`; bộ lọc `classification`
  cho từng nhóm; xin bậc vượt quyền → rỗng; giá trị sai → 422; `soldier` tạo bài MẬT → 403.
- `scripts/export_openapi.py` → `openapi.yaml` v1.9.0, 62 path / 100 operation, param
  `classification` xuất hiện ở `GET /posts`.

## v1.8.0 — 2026-08-30

**Người bàn giao:** Backend
**Phạm vi:** Kênh chuyên BCH & Cấp uỷ — Giao ban trực tuyến & Quản lý cuộc họp Chỉ huy.
**Quy mô:** 62 path / 100 operation.

### RBAC
- Toàn module gác qua `can_access_command_channel` = `has_secret_clearance` (`commander`/`admin` HOẶC
  `User.clearance = True`) → không đủ quyền **403** (kể cả xem lịch, chi tiết, tải tài liệu, cập nhật
  điểm danh của chính mình).
- Tạo / sửa / huỷ cuộc họp, ghi biên bản, điểm danh **người khác**, mời / gỡ thành phần: chỉ
  `commander`/`admin` (`is_command_level`) → 403 nếu khác.
- Thành viên được triệu tập (có quyền MẬT): xem lịch + tài liệu + `meeting_link`, và tự cập nhật
  điểm danh / lý do vắng / ý kiến đóng góp của **chính mình** (`PATCH .../attendees/{user_id}` với
  `user_id == current_user.id`).

### Thêm endpoint (`api/routes/command_meetings.py`, prefix `/command-meetings`)
- `GET /command-meetings` — danh sách; lọc `status_filter`
  (`sap_dien_ra`|`dang_dien_ra`|`da_ket_thuc`|`da_huy`), `date_from`, `date_to`. Kèm `attendee_count`,
  `present_count`, `my_attendance` (điểm danh của người đang đăng nhập nếu là thành phần, ngược lại `null`).
- `POST /command-meetings` (201) — JSON `{ title, start_time, end_time?, location?, meeting_link?,
  agenda?, attendee_user_ids:[] }`. Chỉ `commander`/`admin`. 400 nếu `end_time < start_time`; 404 nếu
  `attendee_user_ids` có tài khoản không tồn tại / đã khoá; 422 nếu `start_time` sai định dạng.
- `GET /command-meetings/{id}` — chi tiết + `attendees[]` (`full_name`, `unit_name`, `attendance`
  `co_mat`|`vang_mat`|`chua_diem_danh`, `absence_reason`, `contribution_note`).
- `PUT /command-meetings/{id}` — sửa (kèm `status`). Chỉ `commander`/`admin`. 400 nếu thời gian sai.
- `DELETE /command-meetings/{id}` (204) — huỷ hẳn (xoá kèm thành phần + tệp). Chỉ `commander`/`admin`.
- `POST /command-meetings/{id}/minutes` (200) — `{ minutes, mark_finished? }` (đặt `status=da_ket_thuc`).
  Chỉ `commander`/`admin`.
- `POST /command-meetings/{id}/attachment` (200) — **multipart** `file` (ảnh/.pdf/.doc/.docx/… →
  `/static/command/…`, thay tệp cũ). Chỉ `commander`/`admin`. 400 nếu định dạng không hợp lệ.
- `GET /command-meetings/{id}/download` — `FileResponse` có kiểm soát quyền MẬT (không qua `/static`).
  404 nếu không có tệp.
- `POST /command-meetings/{id}/attendees` (201) — `{ user_ids:[] }` mời thêm. Chỉ `commander`/`admin`.
  409 nếu đã có trong thành phần; 404 nếu tài khoản không hợp lệ.
- `DELETE /command-meetings/{id}/attendees/{user_id}` (204) — gỡ thành phần. Chỉ `commander`/`admin`.
- `PATCH /command-meetings/{id}/attendees/{user_id}` (200) — `{ attendance?, absence_reason?,
  contribution_note? }`. `commander`/`admin` cho bất kỳ ai; thành viên chỉ cho `user_id` của mình
  (403 nếu khác). 404 nếu không có trong thành phần.

### Schema mới (`schemas/command_meeting.py`)
- Enum `MeetingStatus`, `AttendanceStatus`.
- `CommandMeetingCreate`, `CommandMeetingUpdate`, `MinutesRequest`, `InviteRequest`,
  `AttendanceUpdate`, `AttendeeOut`, `CommandMeetingOut` (+ `attendee_count`, `present_count`,
  `my_attendance`), `CommandMeetingDetailOut` (+ `attendees[]`).

### DB
- 2 bảng mới qua `create_all` (không cần migration): `command_meetings`,
  `command_meeting_attendees` (unique `meeting_id+user_id`).

### Ảnh hưởng Frontend
- Thêm `frontend/src/types/commandMeeting.ts`, `frontend/src/api/commandMeetings.ts`.
- Trang mới `GiaoBanTrucTuyenPage` (route `/giao-ban`) — lịch giao ban sắp tới + nút vào phòng trực
  tuyến (mở `meeting_link`), form tạo/điều hành, đính kèm + tải biên bản/tài liệu, bảng điểm danh
  thành phần cho chỉ huy, ô báo vắng / ý kiến cho thành viên. Nav "Giao ban trực tuyến" hiện khi
  `hasClearance || isCommander`.

### Kiểm thử đã thực hiện
- `from app.main import app` OK (62 path / 100 operation). 2 bảng tạo qua `create_all`.
- Logic + Runtime API: `soldier` / `officer` không clearance → **403** ở mọi endpoint; `officer` có
  clearance → xem/tải tài liệu + tự cập nhật điểm danh/ý kiến của mình được, nhưng **không** tạo/sửa/
  huỷ/ghi biên bản/điểm danh người khác/mời (403); `commander`/`admin` toàn quyền. Chu kỳ: tạo cuộc
  họp + triệu tập → điểm danh (`co_mat`/`vang_mat` + lý do) → ghi biên bản (`mark_finished` →
  `da_ket_thuc`) → upload `.pdf`/`.docx` (thay tệp) → tải về; `end_time < start_time` → 400;
  `start_time` sai → 422; mời trùng → 409; điểm danh người ngoài thành phần → 404; `.exe` → 400;
  no-JWT → 401; `DELETE` → 204; lấy bản đã xoá → 404.
- `scripts/export_openapi.py` → `Da xuat phien ban 1.8.0: 62 path / 100 operation`.

## v1.7.0 — 2026-08-30

**Người bàn giao:** Backend
**Phạm vi:** Kênh chuyên Ban Chỉ huy & Cấp uỷ — trao đổi nội bộ bảo mật cao + Sổ công văn mật.
**Quy mô:** 55 path / 89 operation.

### RBAC toàn module (thay đổi helper `app/core/access.py`)
- `can_access_command_channel(user)` giờ = `has_secret_clearance(user)` (`commander`/`admin` **HOẶC**
  `User.clearance = True`) — **không** còn dùng cờ `command_channel_access`. Không đủ quyền → **403**.
- Thao tác **vào sổ / sửa / xoá / đóng luồng**: chỉ `commander`/`admin` (`is_command_level`) → 403 nếu khác.
- `has_secret_clearance` xem/nộp/ký nhận được.

### Thêm endpoint — Luồng trao đổi BCH (`api/routes/command_threads.py`, prefix `/command-threads`)
- `GET /command-threads` — danh sách (mọi thành viên đủ quyền thấy tất cả; kèm `message_count`,
  `unread_count`, `classification="mat"`).
- `POST /command-threads` (201) — `{ title }`.
- `GET /command-threads/{id}` — luồng + tin nhắn (`skip`/`limit`), tự đánh dấu đã đọc.
- `POST /command-threads/{id}/messages` (201) — **multipart** `body` + `file?` (ảnh/.pdf/.doc/.docx/…
  → `/static/command/…`); 409 nếu luồng đã đóng; 400 nếu trống.
- `PATCH /command-threads/{id}/close` — `{ is_closed }`; chỉ `commander`/`admin`.

### Thêm endpoint — Sổ công văn mật (`api/routes/official_dispatches.py`, prefix `/official-dispatches`)
- `GET /official-dispatches` — danh sách; lọc `direction` (`di`|`den`), `status_filter`
  (`moi`|`dang_xu_ly`|`da_xu_ly`|`luu_tru`).
- `POST /official-dispatches` (201) — **multipart**: `direction`, `dispatch_number`, `summary`,
  `issuing_org?`, `receiving_org?`, `issued_date?`, `received_date?`, `status`, `note?`, `file?`
  (→ `/static/command/…`). Chỉ `commander`/`admin`. 409 nếu trùng `(direction, dispatch_number)`.
- `GET /official-dispatches/{id}` — chi tiết + `acknowledged[]` / `pending[]` (theo danh sách tài
  khoản đang hoạt động có quyền MẬT) + `acknowledged_by_me`.
- `PUT /official-dispatches/{id}` — **multipart** (như POST, `file?` để thay tệp). Chỉ `commander`/`admin`.
- `DELETE /official-dispatches/{id}` (204) — chỉ `commander`/`admin` (xoá kèm tệp + sổ ký nhận).
- `POST /official-dispatches/{id}/acknowledge` (200) — `{ response_note? }`; **upsert** (ký nhận lần
  đầu hoặc cập nhật phản hồi). Mọi tài khoản có quyền MẬT.
- `GET /official-dispatches/{id}/download` — `FileResponse` có kiểm soát quyền (không qua `/static`).

### Schema mới
- `command_thread.py`: `CommandThreadCreate`, `CommandThreadCloseUpdate`, `CommandMessageOut`,
  `CommandThreadOut` (+ `classification`, `message_count`, `unread_count`), `CommandThreadDetailOut`.
- `official_dispatch.py`: `DispatchDirection` (`di|den`), `DispatchStatus`
  (`moi|dang_xu_ly|da_xu_ly|luu_tru`), `DispatchUpdate` (dùng chung tạo & sửa), `AcknowledgeRequest`,
  `DispatchAckOut`, `OfficialDispatchOut` (+ `recipient_count`, `acknowledged_count`,
  `acknowledged_by_me`), `OfficialDispatchDetailOut` (+ `acknowledged[]`, `pending[]`).

### DB
- 5 bảng mới qua `create_all` (không cần migration): `command_threads`, `command_messages`,
  `command_thread_reads` (đọc theo `last_read_message_id`), `official_dispatches`
  (unique `direction+dispatch_number`), `dispatch_acknowledgements` (unique `dispatch_id+user_id`).
- Cột `users.command_channel_access` (thêm ở v1.4.0) **không còn được dùng để gác quyền** — giữ lại
  để tương thích, có thể gỡ sau.

### Ảnh hưởng Frontend
- Thêm `frontend/src/types/commandDispatch.ts`, `frontend/src/api/commandDispatches.ts`.
- Trang mới `KenhChiHuyPage` (route `/kenh-chi-huy`) 2 tab: **Họp bàn BCH & Cấp uỷ** (luồng trao đổi
  mật) + **Sổ công văn mật** (vào sổ, đính kèm, tiến độ ký nhận tiếp thu). Nav mục "Kênh chỉ huy" hiện
  khi `hasClearance || isCommander`. Chip cảnh báo MẬT toàn trang.
- `AuthContext.canCommandChannel` đổi thành `hasClearance || isCommander`; bỏ ô "Kênh chuyên BCH +
  Cấp uỷ" trong form/tbảng `UsersPage` (không còn ý nghĩa).

### Kiểm thử đã thực hiện
- `from app.main import app` OK (55 path / 89 operation). 5 bảng tạo qua `create_all`.
- Logic + Runtime API: `soldier` và `officer` không clearance → **403** ở mọi endpoint (list, get,
  post, acknowledge, download); `officer` có clearance → xem/nộp tin/ký nhận được nhưng **không** tạo
  công văn / đóng luồng (403); `commander`/`admin` → toàn quyền. Multipart gửi tin + `.docx` → 201,
  công văn + `.pdf` → 201; trùng số hiệu → 409; ngày sai định dạng → 422; `acknowledge` upsert cập
  nhật `response_note`; `download` bởi tài khoản đủ quyền → 200, không đủ → 403; đóng luồng rồi gửi →
  409; no-JWT → 401; `PUT` status → 200; `DELETE` → 204; lấy bản đã xoá → 404.
- `scripts/export_openapi.py` → `Da xuat phien ban 1.7.0: 55 path / 89 operation`.

## v1.6.0 — 2026-08-30

**Người bàn giao:** Backend
**Phạm vi:** Kênh Chỉ đạo – Báo cáo — Giao nhiệm vụ & Nộp báo cáo tiến độ.
**Quy mô:** 47 path / 77 operation.

### Thêm endpoint (`api/routes/directive_assignments.py`, prefix `/directive-assignments`, yêu cầu JWT + quyền Kênh Chỉ đạo)
- `GET /directive-assignments` — danh sách. `commander`/`admin` thấy tất cả (lọc `status_filter`,
  `directive_id`); tài khoản được giao chỉ thấy nhiệm vụ có target trùng `unit_id` hoặc `assignee_id`
  của mình (đếm `target_count`/`approved_count`/`pending_count` tính theo phần nhìn thấy). Không có
  quyền kênh → 403.
- `POST /directive-assignments` (201) — **chỉ `commander`/`admin`**. Body `{ directive_id?, title,
  description?, due_date?, targets:[{unit_id, assignee_id?}] }`. 404 nếu `directive_id`/`unit_id` sai.
- `GET /directive-assignments/{id}` — chi tiết + targets + lịch sử submissions. Tài khoản được giao
  chỉ thấy target của mình; ngoài phạm vi → 404.
- `PUT /directive-assignments/{id}` — sửa `title`/`description`/`due_date`/`directive_id`. Chỉ chỉ huy.
- `DELETE /directive-assignments/{id}` (204) — huỷ nhiệm vụ (xoá kèm targets + submissions). Chỉ chỉ huy.
- `POST /directive-assignments/{id}/targets` (201) — thêm đối tượng được giao. Chỉ chỉ huy. 409 nếu trùng.
- `DELETE /directive-assignments/{id}/targets/{target_id}` (200, trả detail) — gỡ đối tượng. Chỉ chỉ huy.
- `POST /directive-assignments/{id}/targets/{target_id}/submit` (201) — **multipart** `content` (bắt
  buộc), `file?` (.pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx hoặc ảnh → `/static/documents/…`). Đặt target
  về `cho_duyet`. Chỉ tài khoản thuộc `unit_id`/`assignee_id` của target (403 nếu khác); 409 nếu target
  đã `da_duyet`; 400 nếu `content` rỗng.
- `POST /directive-assignments/{id}/targets/{target_id}/review` (200) — chỉ chỉ huy. Body
  `{ result: "da_duyet" | "tra_lai", review_note? }`. Ghi kết quả vào lần nộp mới nhất, đổi trạng thái
  target, tự tính lại trạng thái nhiệm vụ. 409 nếu target không ở trạng thái `cho_duyet` / chưa có báo cáo.

### Schema mới
- Enum: `AssignmentStatus` (`chua_giao|dang_thuc_hien|hoan_thanh|qua_han` — `qua_han` là trạng thái
  **suy diễn** khi quá `due_date` và chưa `hoan_thanh`), `TargetStatus`
  (`chua_nop|cho_duyet|da_duyet|tra_lai`), `ReviewResult` (`da_duyet|tra_lai`).
- `TargetCreate`, `DirectiveAssignmentCreate`, `DirectiveAssignmentUpdate`, `ReviewRequest`.
- `SubmissionOut` (`content`, `attachment_url`, `submitted_by_full_name`, `created_at`,
  `review_result`, `review_note`, `reviewed_by_id`, `reviewed_at`).
- `TargetOut` / `TargetDetailOut` (+ `unit_name`, `assignee_full_name`, `status`, `submitted_at`,
  `submission_count`, `submissions[]`).
- `DirectiveAssignmentOut` (+ `directive_title`, `target_count`, `approved_count`, `pending_count`) /
  `DirectiveAssignmentDetailOut` (+ `targets[]`).

### DB
- 3 bảng mới qua `create_all`: `directive_assignments` (FK `directives.id` nullable),
  `directive_assignment_targets` (unique `assignment_id+unit_id+assignee_id`), `directive_submissions`.
  Không cần migration.

### Ảnh hưởng Frontend
- Thêm `frontend/src/types/directiveAssignment.ts`, `frontend/src/api/directiveAssignments.ts`.
- Trang mới `GiaoNhiemVuPage` (route `/giao-nhiem-vu`) — danh sách nhiệm vụ + chi tiết target theo đơn
  vị + form nộp báo cáo đính kèm + modal duyệt/trả lại cho chỉ huy. Nav mục "Giao nhiệm vụ" chỉ hiện
  khi `canDirectiveChannel`.

### Kiểm thử đã thực hiện
- `from app.main import app` OK (47 path / 77 operation). 3 bảng tạo qua `create_all`.
- Logic (gọi thẳng service): tạo sai `unit_id`/`directive_id` → 404; officer tạo/sửa/duyệt → 403;
  tài khoản được giao chỉ thấy target của mình (đơn vị khác → 404, `target_count`=1); vòng
  `chua_nop → cho_duyet → tra_lai → cho_duyet → da_duyet`; review khi chưa có báo cáo / sai trạng thái
  → 409; nộp sau khi `da_duyet` → 409; thêm target trùng → 409; tự tính lại trạng thái nhiệm vụ khi
  thêm/gỡ target & duyệt (`dang_thuc_hien` ↔ `hoan_thanh`); `qua_han` suy diễn đúng theo `due_date`.
- Runtime API (`uvicorn` + curl): no-JWT → 401; multipart submit + `.pdf` → 201
  (`attachment_url=/static/documents/…`), `.exe` → 400, thiếu `content` → 422; officer review → 403,
  admin `tra_lai` → 200, review lại → 409; `PUT` officer → 403 / admin → 200; `GET` thiếu → 404;
  `DELETE` → 204.
- `scripts/export_openapi.py` → `Da xuat phien ban 1.6.0: 47 path / 77 operation`.

## v1.5.0 — 2026-08-30

**Người bàn giao:** Backend
**Phạm vi:** Kênh Chỉ đạo – Báo cáo (BCH Lữ đoàn ↔ đơn vị) — luồng trao đổi 2 chiều theo đơn vị.
**Quy mô:** 41 path / 68 operation.

### Thêm endpoint (`api/routes/directive_threads.py`, prefix `/directive-threads`, yêu cầu JWT)
- `GET /directive-threads` — danh sách luồng nhìn thấy được. BCH/`commander`/`admin` (và tài khoản có
  quyền kênh thuộc đơn vị `bch_lu_doan`) thấy tất cả, lọc `?unit_id=`; tài khoản đơn vị cấp dưới chỉ
  thấy luồng của đơn vị mình. Không có quyền kênh → 403. Kèm `message_count`, `unread_count`, `unit_name`.
- `POST /directive-threads` (201) — tạo luồng. Body `{ unit_id?, title }`. BCH chọn `unit_id` bất kỳ
  (422 nếu thiếu, 404 nếu đơn vị không tồn tại); tài khoản đơn vị bị ép `unit_id` = đơn vị của mình
  (400 nếu chưa được gán đơn vị).
- `GET /directive-threads/{id}` — luồng + danh sách tin nhắn (`skip`/`limit`), tự đánh dấu đã đọc.
  Ngoài phạm vi → 404 (không lộ tồn tại).
- `POST /directive-threads/{id}/messages` (201) — **multipart**: `body` (text, có thể rỗng nếu có
  file), `file` (tuỳ chọn, ảnh hoặc .pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx, lưu `/static/directive/…`).
  400 nếu cả `body` rỗng và không có file; 409 nếu luồng đã đóng.
- `PATCH /directive-threads/{id}/close` — `{ is_closed: bool }`. Chỉ `commander`/`admin` (403 nếu khác).

### Schema mới
- `DirectiveThreadCreate` (`unit_id?: int`, `title`), `ThreadCloseUpdate` (`is_closed`).
- `DirectiveMessageOut` (`id`, `thread_id`, `sender_id`, `sender_full_name`, `body`, `attachment_url`,
  `created_at`).
- `DirectiveThreadOut` (+ `unit_name`, `created_by_full_name`, `last_message_at`, `is_closed`,
  `message_count`, `unread_count`); `DirectiveThreadDetailOut` = `DirectiveThreadOut` + `messages: []`.

### Helper mới (`app/core/access.py`)
- `is_command_level(user)`, `can_access_directive_channel(user)`, `can_access_command_channel(user)`,
  `directive_thread_scope(user)` → `"all" | <unit_id:int> | None`.

### DB
- 3 bảng mới qua `create_all` (không cần migration): `directive_threads`, `directive_messages`,
  `directive_thread_reads` (theo dõi đã đọc bằng `last_read_message_id` — chính xác hơn mốc thời gian).

### Ảnh hưởng Frontend
- Thêm `frontend/src/types/directiveThread.ts`, `frontend/src/api/directiveThreads.ts`.
- Trang mới `ChiDaoBaoCaoPage` (route `/chi-dao-bao-cao`) — danh sách luồng + hội thoại + đính kèm;
  nav mục "Chỉ đạo – Báo cáo" chỉ hiện khi `canDirectiveChannel` (đọc claim `dca`, hoặc là chỉ huy).

### Kiểm thử đã thực hiện
- `from app.main import app` OK (18 route mới). 3 bảng tạo qua `create_all`.
- Logic (gọi thẳng service): `admin`/BCH scope `"all"`; tài khoản đơn vị chỉ thấy luồng đơn vị mình
  (đơn vị khác → 404 khi mở chi tiết, list = 0); không có cờ kênh → 403; tài khoản đơn vị `bch_lu_doan`
  có cờ kênh → scope `"all"` nhưng không đóng luồng được (403 vì không phải chỉ huy); tạo luồng từ tài
  khoản đơn vị bị ép về đúng `unit_id`; `unread_count` 0→1→0 chính xác theo `last_read_message_id`;
  mốc thời gian dùng `func.now()` đồng nhất với phần còn lại.
- Runtime API (`uvicorn` + curl): GET 200 / no-JWT 401 / không cờ kênh 403; POST tạo 201, thiếu
  `unit_id` 422; POST message form 201, kèm `.pdf` 201 (`attachment_url=/static/directive/…`), `.exe`
  400, rỗng 400; tài khoản đơn vị đóng luồng 403, `admin` đóng 200, gửi sau khi đóng 409.
- `scripts/export_openapi.py` → `Da xuat phien ban 1.5.0: 41 path / 68 operation`.

## v1.4.0 — 2026-08-30

**Người bàn giao:** Backend
**Phạm vi:** Nền tảng tổ chức (`units`) + bậc quyền `admin` + 2 cờ kênh hạn chế trên `User` + chính sách mật khẩu.
**Quy mô:** 37 path / 63 operation.

### Thêm / Sửa / Xoá endpoint
- `POST /units/` — tạo đơn vị. Quyền: `admin`. 409 nếu trùng tên.
- `GET /units/` — danh sách đơn vị (mọi tài khoản đã đăng nhập; query `kind`, `active`, `skip`, `limit`).
- `GET /units/{unit_id}` — chi tiết đơn vị (đã đăng nhập). 404 nếu không tồn tại.
- `PUT /units/{unit_id}` — sửa đơn vị. Quyền: `admin`. 409 nếu trùng tên.
- `DELETE /units/{unit_id}` — xoá đơn vị. Quyền: `admin`. 409 nếu còn tài khoản thuộc đơn vị, 404 nếu không tồn tại.
- `PATCH /users/{user_id}/unit` — gán/bỏ đơn vị cho tài khoản. Quyền: `commander`/`admin`. Body `{ unit_id: int | null }`. 404 nếu `unit_id` không tồn tại.
- `PATCH /users/{user_id}/channel-access` — bật/tắt cờ truy cập 2 kênh hạn chế. Quyền: `admin`. Body `{ directive_channel_access?: bool, command_channel_access?: bool }`.
- `POST /users/{user_id}/reset-password` — cấp lại mật khẩu cho tài khoản (đặt `must_change_password=true`). Quyền: `admin`. 204. 422 nếu mật khẩu không đạt chính sách (trừ tài khoản `is_system`).
- `POST /users/` — mở rộng body: thêm `unit_id`, `directive_channel_access`, `command_channel_access`; cho phép `role="admin"` **chỉ khi** người gọi là `admin` (lệch quyền → 403). Tài khoản do người khác tạo → `must_change_password=true`.
- `POST /users/login` — không đổi hình dạng response; JWT bổ sung claim (xem dưới).
- `POST /users/register`, `POST /profile/change-password` — áp chính sách mật khẩu mới (422 nếu yếu); `change-password` khi thành công tự đặt `must_change_password=false`.

### Thay đổi schema
- `UserOut`: thêm `unit_id: int | null`, `unit_name: str | null`, `directive_channel_access: bool`, `command_channel_access: bool`, `is_system: bool`, `must_change_password: bool`.
- `UserCreate`: thêm `unit_id: int | null = null`, `directive_channel_access: bool = false`, `command_channel_access: bool = false`.
- Mới: `UnitCreate`, `UnitOut` (`user_count`), `UnitKind` (`phong_ban|tieu_doan|dai_doi|tram|bch_lu_doan|cap_uy`), `UnitAssignUpdate`, `ChannelAccessUpdate`, `ResetPasswordRequest`.
- `Role` (Literal) thêm giá trị `admin`. `admin` kế thừa toàn bộ quyền của `commander` (áp ở `require_roles`).
- JWT payload thêm: `unit` (unit_id | null), `dca` (bool), `cca` (bool), `mcp` (must_change_password), `adm` (`role=="admin"`).

### Chính sách mật khẩu & tài khoản (mới — `app/core/passwords.py`)
- Mật khẩu ≥ 8 ký tự, có cả chữ và số. Username khớp `^[a-z0-9._-]{3,50}$`.
- Tài khoản `is_system` (admin mặc định) **được miễn** chính sách này.
- Tài khoản admin hệ thống được seed khi chưa có tài khoản `is_system` nào: `SYSTEM_ADMIN_USERNAME`/`SYSTEM_ADMIN_PASSWORD` trong `.env` (mặc định `admin`/`admin`), `role="admin"`, `must_change_password=true`. Không thể khoá / hạ quyền / đổi tài khoản `is_system` (409). Guard "≥ 1 chỉ huy đang hoạt động" tính cả `admin`.

### Ảnh hưởng Frontend
- Cập nhật `frontend/src/types/user.ts` (UserOut/UserCreate + field mới) và thêm `frontend/src/types/unit.ts`.
- Thêm `frontend/src/api/units.ts`; mở rộng `frontend/src/api/users.ts` (setUnit, setChannelAccess, resetPassword).
- `context/AuthContext.tsx`: đọc thêm `unitId`, `canDirectiveChannel` (`dca`), `canCommandChannel` (`cca`), `mustChangePassword` (`mcp`), `isAdmin` (`adm`).
- Màn hình mới `UnitsPage` (route `/quan-ly-don-vi`, chỉ `admin`); `UsersPage` bổ sung cột đơn vị + 2 công tắc kênh + nút cấp lại mật khẩu; luồng buộc đổi mật khẩu khi `mustChangePassword`.

### Migration DB
- Bảng mới `units` tạo qua `create_all`. Bảng `users` cũ: chạy `venv/Scripts/python.exe scripts/migrate_org_and_channels.py` (idempotent) để thêm 5 cột `unit_id`, `directive_channel_access`, `command_channel_access`, `is_system`, `must_change_password`. Chạy **sau** `migrate_access_tiers.py`.
- Seed admin: tự chạy lúc khởi động app; hoặc thủ công `venv/Scripts/python.exe scripts/seed_admin.py`.

### Kiểm thử đã thực hiện
- `from app.main import app` OK (37 route). Migration chạy 2 lần idempotent (lần 2: không thêm cột).
- Logic (gọi thẳng service): seed admin đúng cờ; login `admin/admin` → claim `adm/mcp/clr=true`; mật khẩu thiếu số → 422; username có khoảng trắng → 422; tạo user hợp lệ → `must_change_password=true`, `unit_name` hiển thị qua quan hệ; đổi role tài khoản `is_system` → 409; `reset_user_password` đặt lại cờ; `change_own_password` xoá cờ + áp chính sách (bỏ qua khi `is_system`).
- Runtime API (`uvicorn`, curl): `POST/GET/PUT/DELETE /units` → 201/200/200/204; trùng tên → 409; xoá đơn vị không tồn tại → 404; `GET /units` không JWT → 401; `PATCH /users/{id}/unit` sai id → 404, đúng → 200; `reset-password` → 204, yếu → 422; `officer` gọi endpoint `admin` → 403, `GET /units` → 200.
- `scripts/export_openapi.py` → `Da xuat phien ban 1.4.0: 37 path / 63 operation`.

## v1.3.0 — 2026-08-30

**Người bàn giao:** Backend
**Trạng thái:** Mốc khởi tạo hợp đồng (baseline) — ghi nhận toàn bộ API hiện có.
**Quy mô:** 32 path / 55 operation (theo header `openapi.yaml` sinh lúc 2026-08-30 18:29:05).

### Module đã có trong hợp đồng
- **Người dùng & xác thực** (`users.py`): `POST /users/` (bootstrap `commander` đầu tiên),
  `POST /users/register` (tự đăng ký → `soldier`, `is_active=False`),
  `POST /users/login` (JWT kèm claim `sub`, `role`, `uid`, `clr`),
  `POST /users/{id}/activate` · `/deactivate`, `PATCH /users/{id}/role` · `/clearance`,
  `GET /users/?active=`. Ràng buộc: giữ ≥ 1 `commander` đang `is_active` (409);
  không tự hạ quyền / tự khoá chính mình (400).
- **Hồ sơ cá nhân** (`profile.py`): `GET /profile/me`, `PUT /profile/me`,
  `POST /profile/change-password` (sai mật khẩu cũ → 400, thành công → 204).
- **Tin tức – Hoạt động** (`posts.py`): CRUD `posts` + luồng duyệt
  (`cho_duyet` / `da_duyet` / `tra_lai`), `POST /posts/{id}/review` (chỉ `commander`),
  `POST /posts/{id}/thumbnail` (upload ảnh). Công khai bài `da_duyet` + `cong_khai`.
- **Giáo dục chính trị** (`education_materials.py`): CRUD, có `period_label`, `attachment_url`.
- **Chỉ thị – Nhiệm vụ** (`directives.py`): CRUD (chỉ `commander`), `status` `nhap`/`da_ban_hanh`,
  `POST /directives/{id}/acknowledge` (idempotent),
  `GET /directives/{id}/acknowledgements` (chỉ `commander`).
- **Thông báo nội bộ** (`announcements.py`): CRUD, `priority`, `is_pinned`, `is_public`,
  `starts_at`/`ends_at`, sắp xếp ghim → ưu tiên → mới nhất.
- **Lịch trực kíp** (`duty_schedules.py`): CRUD, lọc `date_from`/`date_to`.
- **Văn bản – Tài liệu – Biểu mẫu** (`documents.py`): upload multipart `POST /documents`,
  `GET /documents/{id}/download` (FileResponse, tôn trọng `classification`).
- **Trang chủ** (`home.py`): `GET /home/summary?limit=`, `GET /home/public`.
- **Items** (`items.py`): CRUD mẫu.

### RBAC & phân loại áp dụng toàn hệ thống
- Role: `commander` / `officer` / `soldier`; helper `app/api/deps.py`.
- 3 bậc `classification`: `cong_khai` / `noi_bo` / `mat`; helper `app/core/access.py`
  (`allowed_classifications`, `can_view_classification`, `has_secret_clearance`).
- Public/Guest (LAN): chỉ các endpoint GET của Tin tức (`da_duyet` + `cong_khai`),
  Thông báo (`is_public`), Tài liệu (`cong_khai`) và `GET /home/public`.

### Hạ tầng liên quan hợp đồng
- `backend/app/core/config.py`: `DATABASE_URL` mã hoá credential bằng `quote_plus`,
  ưu tiên biến `DATABASE_URL` trong `.env` nếu khai báo (đã mã hoá `@` → `%40`).
- Biến `.env` bắt buộc: `MYSQL_HOST/PORT/DATABASE/USER/PASSWORD`, `JWT_SECRET_KEY`.

### Ảnh hưởng Frontend
- `frontend/src/types/` cần phản chiếu đầy đủ các schema `*Create` / `*Out` và
  các enum `role` (`commander|officer|soldier`), `classification`
  (`cong_khai|noi_bo|mat`), `status` bài viết (`cho_duyet|da_duyet|tra_lai`),
  `status` chỉ thị (`nhap|da_ban_hanh`), `priority` thông báo (`thap|binh_thuong|cao|khan`).
- Base URL API: `import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'`.

### Kiểm thử đã thực hiện
- `from app.main import app` OK; `Base.metadata.create_all` tạo 9 bảng trên `ludoan_db`.
- Migration `migrate_access_tiers.py` + `migrate_posts_approval.py`: idempotent, no-op (schema đã đầy đủ).
- Runtime: `uvicorn app.main:app --port 8000` → `GET /` = 200, `GET /home/public` = 200, `GET /docs` = 200.
- `scripts/export_openapi.py` → `openapi.yaml` v1.3.0 (32 path / 55 operation).
