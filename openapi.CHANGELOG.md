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

## v8.1.0 — 2026-09-10

**Người bàn giao:** Backend
**Phạm vi:** Hệ Tin nhắn Tác chiến Nội bộ (`/chats`) — nâng cấp 4 nhóm tính năng:
tương tác trên tin nhắn, quản trị nhóm, realtime nâng cao, tìm kiếm & tiện ích.
`115 path / 162 operation`. **Cần chạy migration DB**:
`backend/scripts/migrate_chat_features.py` (idempotent — thêm cột `chat_messages`
+ `chat_participants`, tạo bảng `chat_message_reactions`, đặt FK tự tham chiếu
`reply_to_id` / `forwarded_from_id` / `pinned_by_id` = `ON DELETE SET NULL`).

Bump **MINOR**: chỉ thêm endpoint mới + thêm field response/optional — client cũ
không vỡ (mọi field mới có default; `reply_to_id` trong body là tuỳ chọn).

### Thêm endpoint
- `PATCH /chats/{id}/messages/{message_id}` — sửa nội dung tin nhắn. Chỉ người gửi;
  tin hệ thống hoặc đã thu hồi → **409**; người khác sửa → **403**. Đẩy realtime `message:edit`.
- `DELETE /chats/{id}/messages/{message_id}` — thu hồi tin nhắn (204). Người gửi
  **hoặc** quản trị viên nhóm **hoặc** Ban chỉ huy (`role 0–3`); khác → **403**.
  Xoá nội dung + tệp đính kèm, giữ ô trống "đã thu hồi". Đẩy realtime `message:recall`.
- `POST /chats/{id}/messages/{message_id}/reactions` — thả cảm xúc (`{emoji}`), idempotent.
- `DELETE /chats/{id}/messages/{message_id}/reactions?emoji=` — gỡ cảm xúc.
  Cả hai trả `ChatMessageOut` (đã gộp `reactions`) + đẩy `message:react`.
- `POST /chats/{id}/messages/{message_id}/pin` — ghim/bỏ ghim (`{pinned}`). Nhóm:
  quản trị viên nhóm / Ban chỉ huy → **403** nếu khác; 1-1: cả hai bên. Đẩy `message:pin`.
- `GET /chats/{id}/pinned` — danh sách tin đã ghim (`ChatMessageOut[]`).
- `POST /chats/{id}/messages/{message_id}/forward` — chuyển tiếp sang hội thoại đích
  (`{target_conversation_id}`, 201). Phải là thành viên **cả hai** hội thoại → **403**;
  tin đã thu hồi / tin hệ thống → **409**. Đẩy `message:new` sang hội thoại đích.
- `GET /chats/{id}/messages/search?q=&skip=&limit=` — tìm tin trong một hội thoại (thành viên → **403**).
- `GET /chats/search?q=&limit=` — tìm tin trên mọi hội thoại người gọi tham gia.
- `PATCH /chats/{id}` — đổi tên nhóm (`{name}`). Quản trị viên nhóm / Ban chỉ huy → **403**;
  sinh 1 tin hệ thống (`message_type="system"`) + đẩy `message:new`.
- `PATCH /chats/{id}/members/{user_id}/role` — phong/gỡ quản trị viên nhóm (`{is_admin}`).
  Người tạo nhóm / Ban chỉ huy → **403**; đổi quyền người tạo nhóm → **409**;
  thành viên không có trong nhóm → **404**.
- `POST /chats/{id}/mute` — tắt/bật thông báo hội thoại cho chính người gọi (`{muted}`).
- `POST /chats/{id}/archive` — lưu trữ/bỏ lưu trữ hội thoại cho chính người gọi (`{archived}`).
- `GET /chats/{id}/receipts` — mốc đọc từng thành viên (`ReadReceiptOut[]`) để hiển thị "Đã xem".

### Sửa endpoint sẵn có (không phá vỡ)
- `GET /chats` — thêm query `archived: bool = false`. Mặc định **ẩn** hội thoại người
  gọi đã tự lưu trữ; `?archived=true` chỉ hiện hội thoại đã lưu trữ.
- `POST /chats/{id}/messages` — body thêm `reply_to_id: int | null` (trả lời/trích dẫn);
  sai id → **404**.
- `POST /chats/{id}/messages/upload` — form thêm `reply_to_id` (tuỳ chọn).
- `POST /chats/{id}/read` — nay trả `{ok, last_read_message_id}` và đẩy realtime `read`.
- `POST /chats/{id}/members`, `DELETE /chats/{id}/members/{user_id}` — thêm/bớt/rời nhóm
  nay sinh tin hệ thống và đẩy realtime.
- Tin `message_type="system"` **không** tính vào `unread_count`.

### Thay đổi schema
- `ChatMessageOut` thêm: `message_type` (`"user"|"system"`), `reply_to` (`ReplyPreviewOut|null`),
  `forwarded_from` (`ReplyPreviewOut|null`), `reactions` (`ReactionOut[]`), `is_edited`,
  `edited_at`, `is_recalled`, `recalled_at`, `is_pinned`, `pinned_at`.
- `ChatConversationOut` thêm: `is_muted`, `is_archived`, `other_user_online` (bool, default `false`).
- `ChatParticipantOut` thêm: `is_online` (bool, default `false`).
- `ChatMessageCreate` thêm: `reply_to_id` (`int|null`, tuỳ chọn).
- Schema mới: `ChatMessageEditPayload`, `ChatReactionPayload`, `ChatMessagePinPayload`,
  `ChatForwardPayload`, `GroupRenamePayload`, `MemberRolePayload`, `MutePayload`,
  `ArchivePayload`, `ReactionOut`, `ReplyPreviewOut`, `ReadReceiptOut`.

### WebSocket `/chats/ws` (không mô tả trong openapi.yaml)
- Server → client thêm sự kiện: `message:edit`, `message:recall`, `message:react`,
  `message:pin`, `read`, `typing`, `presence`.
- Client → server nhận thêm JSON `{"type":"typing","conversation_id":N}` (vẫn giữ chuỗi `"ping"`).
- Khi mở/đóng kết nối: phát `presence` `{user_id, online}` tới các quân nhân có chung hội thoại.

### Ảnh hưởng Frontend
- Cập nhật `fe-ludoan/src/types/chat.ts` (mở rộng `ChatMessage`, `ChatConversation`,
  `ChatParticipant`, `ChatSocketEvent` + payload mới), `fe-ludoan/src/api/chats.ts`
  (14 hàm mới), `fe-ludoan/src/api/chatSocket.ts` (gửi `typing`), `fe-ludoan/src/pages/TinNhanPage.tsx`.
- Màn hình bị ảnh hưởng: trang Tin nhắn (`/tin-nhan`).

### Kiểm thử đã thực hiện
- `scripts/test_chat_features.py` (mới, 44 case): reply/edit/recall + nhánh 403/409,
  toggle reaction idempotent, ghim + `list_pinned` + 403, forward (2 đầu) + 403/409,
  search + bỏ tin thu hồi, rename + sinh tin hệ thống + 403, phong/gỡ QTV (409 người
  tạo, 404 ngoài nhóm, 403), mute/archive (ẩn/hiện danh sách), receipts + 403,
  tin hệ thống khi thêm/bớt thành viên, broadcast helpers chạy trơn.
- `scripts/run_all_tests.py`: 4/4 suite PASS (292 case) — đã thêm `test_chat_features`.
- Regression: `test_chat_system.py`, `test_chat_add_member_validation.py` PASS
  (cập nhật `mark_read` route → `async`).
- Runtime (uvicorn + MySQL): login → tạo 1-1/nhóm → reply/edit/reaction/pin/pinned/
  forward/receipts/mute/archive/search/rename/role trả 200/201/204 đúng; thu hồi 204;
  xoá nhóm có tin được hội thoại khác chuyển tiếp → 204 (FK `SET NULL` hoạt động).
- Migration `migrate_chat_features.py` chạy 2 lần: lần 2 "không có gì để thêm" (idempotent).

---

## v8.0.0 — 2026-09-10

**Người bàn giao:** Backend
**Phạm vi:** Đợt kiểm định toàn bộ module tính năng — vá lỗ hổng phân quyền + chuẩn hoá
mô hình trạng thái. `104 path / 148 operation` (không đổi số lượng). Không cần
migration DB (không thêm/đổi cột — chỉ siết validate ở tầng schema/service).

Bump **MAJOR** vì `LeadershipTaskReview.status` đổi từ `str` tự do → `enum` (theo bảng
quy ước ở đầu file). Client hợp lệ (FE) không bị ảnh hưởng: vẫn chỉ gửi
`da_hoan_thanh` / `can_bo_sung`.

### Sửa / siết endpoint (hành vi, không đổi path/method)
- `POST /leadership-tasks/{id}/report` — **thêm chốt quyền** (F2): trả **403** nếu người
  nộp không thuộc đơn vị / khối–ngành được giao (tài khoản `role=5` luôn bị chặn).
  Ban Chỉ huy (`role 0–3`) và cán bộ đúng đơn vị/ngành mới nộp được. Nộp báo cáo giờ
  chuyển trạng thái `dang_thuc_hien → da_bao_cao` (F3).
- `GET /leadership-tasks` — **thu hẹp phạm vi xem** (F4): `role 0–3` thấy mọi chỉ đạo;
  `role 4–5` chỉ thấy chỉ đạo giao cho đơn vị mình **hoặc** chỉ đạo phạm vi rộng
  (`assigned_unit_id=null`) thuộc `toan_lu_doan` / khối–ngành mình phụ trách. `total`
  phân trang tính theo đúng phạm vi.
- `GET /leadership-tasks/{id}` — trả **404** nếu chỉ đạo ngoài phạm vi xem của tài khoản
  (không lộ sự tồn tại) (F4).
- `POST /duty-shift-handovers/{id}/acknowledge` — **thêm chốt quyền + guard trạng thái**
  (F7): **409** nếu biên bản không còn `cho_nhan` (đã ký / đã có ý kiến chỉ huy);
  **403** với người không phải người-nhận-được-chỉ-định / không phải cán bộ trong biên
  chế; người lập biên bản không tự ký nhận.
- `POST /duty-shift-handovers` — chặn tài khoản `role=5` (**403**); chặn tự bàn giao cho
  chính mình (**400**) (F7).
- `POST /chats/{id}/members` — **404** nếu `user_id` không tồn tại / đã bị khoá (không còn
  sinh bản ghi `ChatParticipant` mồ côi) (F5).

### Thay đổi schema
- `LeadershipTaskReview.status`: `str` → `enum [da_hoan_thanh, can_bo_sung]` (default
  `da_hoan_thanh`). Giá trị khác → **422**.
- `LeadershipTaskCreate.commander_role`: `str` → `enum [lu_truong, chinh_uy, lu_pho_tmt,
  lu_pho_hckt, pho_chinh_uy]`.
- `LeadershipTaskCreate.target_branch`: `str` → `enum [tham_muu, chinh_tri,
  hau_can_ky_thuat, toan_lu_doan]` (default `toan_lu_doan`).
- `LeadershipTaskCreate.urgency`: `str` → `enum [hoa_toc, khan, thuong]` (default `thuong`).
- `LeadershipTaskOut.status` bổ sung giá trị `da_bao_cao` (vòng đời:
  `dang_thuc_hien → da_bao_cao → da_hoan_thanh | can_bo_sung`); `status_label` có nhãn
  "Đã báo cáo, chờ bút phê". Kiểu khai báo giữ `str` (đọc dữ liệu cũ không vỡ).
- Tham số truy vấn `GET /leadership-tasks?status=` mô tả lại đúng 4 giá trị hợp lệ.

### Ảnh hưởng Frontend (`fe-ludoan/`)
- `src/types/` (Bàn làm việc BCH): `LeadershipTaskReview.status` = `'da_hoan_thanh' |
  'can_bo_sung'`; `commander_role` / `target_branch` / `urgency` chuyển sang union literal;
  `LeadershipTask.status` thêm `'da_bao_cao'`; bổ sung nhãn trạng thái mới.
- UI: sau khi đơn vị nộp báo cáo, chip trạng thái hiển thị "Đã báo cáo, chờ bút phê";
  danh sách/chi tiết chỉ đạo với tài khoản `role 4–5` nay chỉ còn phần của đơn vị/ngành
  mình — rà lại thông báo rỗng và bộ lọc. Xử lý 403 (nộp báo cáo ngoài phạm vi), 404
  (mở chi tiết ngoài phạm vi), 409 (ký nhận biên bản đã chốt).
- Không có endpoint mới → tầng `src/api/` không đổi chữ ký hàm.

### Kiểm thử đã thực hiện (tầng service, SQLite in-memory + regression)
- `scripts/test_leadership_report_rbac.py` (mới) — F2 (7) + F3 (5) + F4 (13) case: chốt
  quyền nộp báo cáo, siết enum trạng thái, vòng đời `da_bao_cao`, phạm vi xem list/detail
  theo đơn vị/khối–ngành, 404 ngoài phạm vi. **TẤT CẢ PASS.**
- `scripts/test_duty_handover_ack_rbac.py` (mới) — F7, 11 case: guard `cho_nhan` → 409,
  đúng người nhận / cán bộ biên chế / BCH mới ký, chặn `role 5` lập & ký, chặn tự bàn
  giao. **PASS.**
- `scripts/test_chat_add_member_validation.py` (mới) — F5: thêm `user_id` lạ / tài khoản
  khoá → 404, không sinh participant mồ côi. **PASS.**
- `scripts/test_duty_week_plan_timestamps.py` (mới) — F6: `submitted_at` / `reviewed_at`
  dùng `datetime.now()` (đồng bộ `func.now()` của MySQL), hết lệch múi giờ do
  `datetime.utcnow()`. **PASS.**
- Regression: `test_post_rbac`, `test_leadership_tasks` (đã cập nhật theo enum mới),
  `test_duty_shift_handover`, `test_chat_system`, `test_audit_log`, `test_rbac_branches`,
  `test_secure_dispatch_storage`, `test_upload_security`, `test_user_bulk_operations`,
  `test_rate_limit` — **TẤT CẢ PASS.**
- Phụ trợ: `app/models/__init__.py` nay nạp đủ mọi model (mapper) → sửa lỗi
  `InvalidRequestError: 'DutyPlanAttachment' is not defined` khi script test chỉ import
  một phần model. `app.openapi()` = 104 path / 148 operation, `version` = 8.0.0.

---

## v7.13.0 — 2026-09-08

**Người bàn giao:** Backend
**Phạm vi:** Lịch trực — đính kèm **nhiều tệp mọi loại** vào từng bảng trực tuần (`duty_week_plans`).
104 path / 148 operation (+2 path, +3 operation). Model DB: **thêm bảng mới** `duty_plan_attachments` (tự tạo bằng `create_all`, không cần migration thủ công).

### 1. Model DB mới — `duty_plan_attachments`
- `id` PK, `week_plan_id` INT NOT NULL (FK `duty_week_plans.id`, ON DELETE CASCADE, index),
  `file_url` VARCHAR(500) NOT NULL (`/static/duty-plans/<uuid>.<ext>`),
  `original_name` VARCHAR(255) NOT NULL, `file_size` INT NOT NULL DEFAULT 0,
  `content_type` VARCHAR(100) NULL, `label` VARCHAR(200) NULL (mô tả ngắn),
  `uploaded_by_id` INT NOT NULL (FK `users.id`), `created_at` DATETIME NOT NULL.
- Quan hệ `DutyWeekPlan.attachments` (`cascade="all, delete-orphan"`); xoá bảng trực → xoá tệp DB + tệp vật lý.

### 2. Thêm endpoint (router `/duty-week-plans`, đều cần JWT)
- `GET /duty-week-plans/{plan_id}/attachments` — danh sách tệp đính kèm của bảng trực. Quyền xem = quyền xem bảng trực (`_require_visible`): chỉ huy/quản trị xem mọi bảng; đơn vị khác chỉ xem bảng `da_duyet`; ngoài phạm vi → 404.
- `POST /duty-week-plans/{plan_id}/attachments` — **multipart** `file` (bắt buộc) + `label` (Form, tuỳ chọn, ≤ 200). Role: `CONTENT_ROLES` (0–4) ở tầng route; tầng service `_require_owner_unit` (đúng đơn vị sở hữu hoặc chỉ huy) → 403 nếu khác. Cho phép đính kèm ở **mọi trạng thái** bảng trực (kể cả `da_duyet` — để gắn bản ký). Định dạng cho phép: `.pdf .doc .docx .xls .xlsx .ppt .pptx .jpg .jpeg .png .webp .gif` (sai định dạng/chữ ký nhị phân → 400; quá `MAX_UPLOAD_MB` → 400). Trả `DutyPlanAttachmentOut` (201).
- `DELETE /duty-week-plans/{plan_id}/attachments/{attachment_id}` — 204. Chỉ **người tải lên** hoặc **chỉ huy/quản trị** (`_is_command_level`) → 403 nếu khác; `attachment_id` không thuộc `plan_id` → 404. Xoá cả tệp vật lý.

### 3. Thay đổi schema
- **Mới** `DutyPlanAttachmentOut { id, week_plan_id, file_url, original_name, file_size, content_type?, label?, uploaded_by_id, uploaded_by_name, created_at }`.
- **Mới** `DutyPlanAttachmentCreate { label? }` (metadata multipart, tài liệu hoá hợp đồng).
- `DutyWeekPlanOut`: **thêm** `attachment_count: int`.
- `DutyWeekPlanDetail`: **thêm** `attachments: DutyPlanAttachmentOut[]`.

### 4. Ảnh hưởng Frontend
- `fe-ludoan/src/types/dutySchedule.ts`: thêm `DutyPlanAttachment`; `DutyWeekPlan` thêm `attachment_count`; `DutyWeekPlanDetail` thêm `attachments`.
- `fe-ludoan/src/api/dutySchedules.ts`: `listPlanAttachments(planId)`, `uploadPlanAttachment(planId, file, label?)`, `deletePlanAttachment(planId, attachmentId)`.
- `fe-ludoan/src/pages/DutyRosterPage.tsx`: khu vực "Tệp đính kèm" trong chi tiết bảng trực (thẻ "Lập & duyệt bảng trực") — kéo–thả / chọn tệp, danh sách tệp có nút tải về (`/static`) + xoá (`useConfirm`), badge số tệp trên danh sách bảng trực.

### 5. Kiểm thử đã thực hiện
- `app.openapi()` = 104 path / 148 operation; bảng `duty_plan_attachments` tạo trên MySQL (utf8mb4, 2 FK đúng).
- Test tầng service (MySQL thật): tạo bảng trực → upload `.pdf` + `.xlsx` → `list` = 2 → `DutyWeekPlanDetail.attachment_count` = 2 → user khác đơn vị upload → 403 → xoá 1 tệp (file vật lý mất) → xoá `attachment_id` lạ → 404 → `delete_plan` cascade xoá tệp DB + tệp vật lý. **Tất cả PASS.**
- Runtime: uvicorn khởi động sạch; `GET`/`POST .../attachments` không JWT → 401; `openapi.json` phiên bản 7.13.0.
- Regression `scripts/test_post_rbac.py` — **TẤT CẢ PASS**.

---

## v7.12.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Tin nhắn Tác chiến — **duyệt nhóm chờ** + **xoá nhóm** + siết quyền xoá thành viên.
102 path / 145 operation (+3 endpoint REST). Model DB: thêm 4 cột vào `chat_conversations` (migration thủ công).

### 1. Thay đổi model DB (`chat_conversations`)
- `status` VARCHAR(20) NOT NULL DEFAULT `'da_duyet'` (index) — `da_duyet` | `cho_duyet` | `tu_choi`.
- `review_note` VARCHAR(500) NULL — lý do từ chối.
- `reviewed_by_id` INT NULL (FK `users.id`), `reviewed_at` DATETIME NULL.
- **Migration bắt buộc (bảng cũ):** `venv/Scripts/python scripts/migrate_chat_group_approval.py` (idempotent; hàng cũ → `status='da_duyet'`). Bảng mới dùng `create_all`.

### 2. Luồng duyệt nhóm
- `POST /chats/group` — **không đổi chữ ký**. Người tạo là **`is_command`** (role 0–3) → nhóm `status='da_duyet'` dùng ngay (như trước). Người tạo role **4–5** → nhóm `status='cho_duyet'`.
- Nhóm `cho_duyet` / `tu_choi` **chỉ hiện với người tạo** trong `GET /chats` (thành viên khác không thấy tới khi duyệt). `GET /chats/{id}/messages`, `POST /chats/{id}/messages`, `POST /chats/{id}/messages/upload`, `POST /chats/{id}/members` vào nhóm chưa `da_duyet` → **409**.

### 3. Endpoint mới
- `GET /chats/pending-groups` — danh sách nhóm `cho_duyet`. Quyền: `CHAT_GROUP_APPROVE_ROLES` = role **0, 1** (Quản trị hệ thống, Lữ trưởng – Chính uỷ) → **403** nếu khác.
- `POST /chats/{id}/review` — body `GroupReviewPayload { approve: bool, note?: str≤500 }`. Quyền role **0, 1**. `approve=true` → `status='da_duyet'`; `approve=false` → `status='tu_choi'` + `review_note` (**BẮT BUỘC** có lý do, thiếu → **400**). Nhóm không ở `cho_duyet` → **409**. Nhóm không tồn tại/không phải group → **404**. Trả `ChatConversationOut`. Ghi `audit_logs` (`CHAT_GROUP_APPROVED`/`CHAT_GROUP_REJECTED`).
- `DELETE /chats/{id}` — **204**. Xoá cứng nhóm + cascade toàn bộ `chat_participants`, `chat_messages`, và `delete_upload` mọi tệp đính kèm. Quyền: **người tạo nhóm** (`created_by_id`) HOẶC **Quản trị hệ thống (role 0)** → **403** nếu khác; **404** nếu không tồn tại/không phải group. Ghi `audit_logs` (`CHAT_GROUP_DELETED`).

### 4. Sửa quyền endpoint sẵn có
- `DELETE /chats/{id}/members/{user_id}` — quyền mới: **tự rời nhóm** (mọi thành viên) HOẶC **người tạo nhóm / Quản trị hệ thống (role 0)** xoá thành viên khác (trước đây là quản trị viên nhóm hoặc role ≤ 2). Vào nhóm chưa `da_duyet`: `POST /chats/{id}/members` → 409.

### 5. Thay đổi schema
- `ChatConversationOut`: **thêm** `status: str` (mặc định `"da_duyet"`), `review_note: str | null`, `reviewed_by_id: int | null`.
- **Mới** `GroupReviewPayload { approve: bool, note: str | null }`.

### 6. Ảnh hưởng Frontend
- `fe-ludoan/src/types/chat.ts`: `ChatConversation` thêm `status` / `review_note` / `reviewed_by_id`; union `ChatGroupStatus`; type `GroupReviewPayload`.
- `fe-ludoan/src/api/chats.ts`: `listPendingGroups()`, `reviewGroup(id, payload)`, `deleteGroup(id)`.
- `fe-ludoan/src/pages/TinNhanPage.tsx`: nhãn "Chờ duyệt"/"Bị từ chối" ở danh sách; khoá ô nhập + hiện thông báo (kèm lý do) với nhóm chưa `da_duyet`; khối "Nhóm chờ duyệt (N)" cho role 0–1 với nút Duyệt / Từ chối (nhập lý do); nút "Xoá nhóm" + nút xoá từng thành viên trong drawer cho người tạo / admin (dùng `useConfirm` / `usePrompt`).

### 7. Kiểm thử đã thực hiện
- `py_compile` sạch; migration chạy (thêm 4 cột + index + FK); `app.openapi()` = 102 path / 145 operation.
- Script test tay 13 case: is_command tạo → `da_duyet`; role5 tạo → `cho_duyet`; gửi tin nhóm chờ → 409; role5 xem pending-groups → 403; admin xem → thấy; từ chối thiếu lý do → 400; từ chối có lý do → `tu_choi`+note; review lại nhóm `tu_choi` → 409; duyệt → role5 gửi tin OK (201); người tạo xoá nhóm mình → 204; người khác xoá → 403; admin xoá → 204. **Tất cả PASS.**

---

## v7.11.1 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Tin nhắn Tác chiến — gửi tệp đính kèm cho phép thêm **tệp nén** (`.zip .rar .7z .tar .gz .bz2`). Không thêm/xoá endpoint, không đổi model DB, không đổi hình dạng dữ liệu request/response → **PATCH**.
99 path / 142 operation (không đổi).

### 1. Thay đổi hành vi
- `POST /chats/{id}/messages/upload` — danh sách định dạng `file` cho phép mở rộng: **ảnh** `.jpg .jpeg .png .webp .gif` · **tài liệu** `.pdf .doc .docx .xls .xlsx .ppt .pptx` · **video** `.mp4 .webm .ogg .mov .m4v` · **tệp nén** `.zip .rar .7z .tar .gz .bz2`.
  - `app/core/uploads.py`: thêm hằng `ARCHIVE_EXTENSIONS`; `validate_magic_bytes` kiểm tra chữ ký nhị phân từng loại nén (ZIP `PK\x03\x04`/`PK\x05\x06`/`PK\x07\x08`, RAR `Rar!\x1a\x07`, 7z `7z\xbc\xaf\x27\x1c`, GZIP `\x1f\x8b`, BZIP2 `BZh`, TAR `ustar` tại offset 257). Sai chữ ký → **400**. Các chặn tuyệt đối (MZ/PE, ELF, Java Class, web shell) giữ nguyên.
  - Hạn mức dung lượng: video **và tệp nén** dùng `MAX_VIDEO_UPLOAD_MB` (mặc định lớn); ảnh/tài liệu vẫn `MAX_UPLOAD_MB`.
  - Mô tả (description) của endpoint trong `openapi.yaml` cập nhật theo docstring mới.

### 2. Ảnh hưởng Frontend
- `fe-ludoan/src/pages/TinNhanPage.tsx`: `DOC_ACCEPT` (thuộc tính `accept` của ô chọn tệp) thêm `.zip,.rar,.7z,.tar,.gz,.bz2`; thẻ tệp đính kèm thêm thuộc tính `download` để tải đúng tên gốc.

### 3. Đồng bộ hợp đồng
- Chạy lại `scripts/export_openapi.py`. Lưu ý: `openapi.yaml` trước đó còn ở header `v1.9.1 / 62 path` (các đợt bàn giao v7.x trước ghi CHANGELOG nhưng **chưa** xuất lại file). Lần xuất này đưa `openapi.yaml` khớp backend hiện tại: **v7.11.1 / 99 path / 142 operation** (diff lớn là do dồn nhiều đợt trước, không riêng thay đổi này).

### 4. Kiểm thử đã thực hiện
- `python -m py_compile` sạch. Xuất `openapi.yaml` thành công (99 path / 142 operation).
- Test tay: upload `.zip` hợp lệ vào hội thoại → `201`, `attachment_url = /static/chat/<uuid>.zip`, `GET` tệp tĩnh → `200`; `.zip` sai chữ ký (đổi đuôi từ tệp khác) → `400`.

---

## v7.11.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Tin nhắn Tác chiến — gửi tệp đính kèm thật (ảnh / tài liệu / video) trong hội thoại 1-1 và nhóm.
99 path / 142 operation (+1 endpoint REST). Không đổi model DB (dùng lại 2 cột `attachment_url`, `attachment_name` đã có trên `chat_messages` từ v7.8.0).

### 1. Endpoint mới
- `POST /chats/{id}/messages/upload` — multipart `content` (str, chú thích tuỳ chọn) + `file` (bắt buộc: ảnh `.jpg .jpeg .png .webp .gif` / tài liệu `.pdf .doc .docx .xls .xlsx .ppt .pptx` / video `.mp4 .webm .ogg .mov .m4v`). Lưu qua `save_upload(subdir="chat")` → `/static/chat/<uuid>.<ext>` (quét magic-byte + chặn web shell như mọi upload khác). Video dùng hạn mức `MAX_VIDEO_UPLOAD_MB`, còn lại `MAX_UPLOAD_MB`.
  - Quyền: là thành viên hội thoại (`Depends(get_current_user)` ở router + kiểm tra participant ở service). **Không** giới hạn theo `role` — role 5 vẫn gửi được tệp trong hội thoại của mình (khác `POST /api/upload` vốn chỉ cho `CONTENT_ROLES`).
  - Trả về `ChatMessageOut` (kèm `attachment_url` / `attachment_name`); nếu bỏ trống `content` → `content = "📎 <tên tệp gốc>"`.
  - Sau khi lưu, đẩy `message:new` qua `WS /chats/ws` tới thành viên online (giống `POST /chats/{id}/messages`).
  - Mã lỗi: sai định dạng / quá dung lượng / tệp rỗng → **400**; không phải thành viên hội thoại → **403** (và tệp vừa lưu bị `delete_upload` dọn ngay).

### 2. Schema
- Không thêm/sửa Pydantic schema thủ công. FastAPI tự sinh `Body_send_message_with_file_chats__id__messages_upload_post` (multipart) trong `openapi.yaml` từ khai báo `Form`/`File` của route.

### 3. Ảnh hưởng Frontend
- `fe-ludoan/src/api/chats.ts`: thêm `chatsApi.sendFile(conversationId, file, content?)` → `postForm('/chats/{id}/messages/upload')`.
- `fe-ludoan/src/pages/TinNhanPage.tsx`: nút "Tệp" / "Ảnh" gọi upload thật (bỏ `URL.createObjectURL` mô phỏng); chèn tin trả về vào khung chat (khử trùng lặp theo `id`); ảnh `/static/...` được ghép tiền tố `VITE_API_BASE_URL` khi hiển thị. Đồng thời bỏ toàn bộ dữ liệu hội thoại/tin nhắn giả (mock) — trang chỉ chạy trên dữ liệu thật từ `GET /chats`, `GET /users`.

### 4. Kiểm thử đã thực hiện
- Import sạch; `POST /chats/{id}/messages/upload` xuất hiện trong `app.openapi()` (99 path / 142 operation).
- Test tay: `save_upload` PNG hợp lệ → `/static/chat/<uuid>.png`; `send_file_message` có caption → `content` = caption đã trim + `attachment_url`/`attachment_name` đúng; caption rỗng → `content = "📎 <tên tệp>"`; `broadcast_new_message` phát `message:new`; người ngoài hội thoại → **403** và tệp vừa lưu bị xoá khỏi đĩa. `scripts/test_chat_system.py` PASS 100% (không hồi quy). Hội thoại + tệp test đã dọn.

---

## v7.10.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Kênh Tin nhắn Tác chiến thời gian thực (WebSocket) — tin nhắn nhóm & 1-1 hiển thị ngay cho thành viên đang online, không cần F5 / polling.
98 path / 141 operation (REST không đổi). Bổ sung 1 endpoint **WebSocket** `WS /chats/ws` (WebSocket không nằm trong `openapi.yaml` — OpenAPI không mô tả giao thức WS; ghi lại hợp đồng ở mục này).

### 1. Endpoint mới
- `WS /chats/ws?token=<JWT>` — kênh đẩy thời gian thực. Không gắn `Depends(get_current_user)` (WebSocket trình duyệt không gửi header `Authorization`); xác thực bằng token JWT ở query-string (`app.api.deps.resolve_ws_user`). Token sai/thiếu → server `accept` rồi `close(1008)`.
  - **Server → client:**
    - `{"type": "ready", "user_id": <int>}` — ngay sau khi kết nối.
    - `{"type": "message:new", "message": <ChatMessageOut>}` — khi có tin nhắn mới trong bất kỳ hội thoại nào tài khoản tham gia. Gửi cho **mọi** thành viên (kể cả người gửi, để đồng bộ đa thiết bị); `message.is_me` luôn `false` — client tự tính lại theo `sender_id`, và tự khử trùng lặp theo `message.id` (vì REST `POST /chats/{id}/messages` đã trả về bản ghi cho người gửi).
    - `{"type": "pong"}` — đáp lại `ping`.
  - **Client → server:** chuỗi văn bản `"ping"` (~25s/lần) để giữ kết nối; các khung khác bị bỏ qua.

### 2. Endpoint thay đổi hành vi (không đổi hợp đồng REST)
- `POST /chats/{id}/messages` — sau khi lưu tin nhắn, đẩy sự kiện `message:new` qua `/chats/ws` tới các thành viên đang online (`chat_service.broadcast_new_message`). Request/response y hệt v7.8.0.

### 3. Schema
- Không thêm/sửa Pydantic schema. Payload WS `message` dùng đúng `ChatMessageOut` hiện có.

### 4. Ảnh hưởng Frontend
- Thêm `fe-ludoan/src/api/chatSocket.ts` (client WS: tự nối lại + heartbeat).
- `fe-ludoan/src/types/chat.ts`: thêm union `ChatSocketEvent`.
- `fe-ludoan/src/pages/TinNhanPage.tsx`: mở WS khi vào trang, nghe `message:new` → chèn tin vào hội thoại đang mở (khử trùng lặp theo `id`) và cập nhật preview/`unread_count` ở danh sách; hiển thị trạng thái kết nối realtime.
- Không cần đổi `openapi.yaml` types (không có schema mới).

### 5. Kiểm thử đã thực hiện
- Import sạch (`from app.main import app`), `Base.metadata.create_all` chạy không lỗi.
- Test cấp ASGI (`scope type=websocket`): token sai → `accept` + `close`; token đúng → khung `ready` đúng `user_id`; gọi `chat_service.send_message` + `broadcast_new_message` → socket nhận `message:new` đúng `content`/`conversation_id`, `is_me=false`; sau `websocket.disconnect` → `ChatConnectionManager` dọn kết nối (`is_online=False`). Hội thoại test đã xoá khỏi DB.
- Lưu ý nợ kỹ thuật đã xử lý luôn: `openapi.yaml` trong repo trước đó vẫn ở **v1.9.1 / 62 path** (các bản v7.8.0–v7.9.0 chỉ ghi CHANGELOG mà chưa chạy `export_openapi.py`). Lần xuất này đưa hợp đồng về đúng hiện trạng backend (98 path / 141 operation) nên diff `openapi.yaml` lớn — phần lớn là các endpoint đã tồn tại từ v7.8.0/v7.9.0 nay mới được ghi vào hợp đồng, không phải thay đổi mới của v7.10.0.

---

## v7.9.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Nâng cấp Quản lý Người dùng: Phân quyền Admin toàn năng, Bộ tài khoản mẫu Lữ đoàn 21, Xoá thủ công/hàng loạt, & Nhập người dùng từ Excel/Word.
98 path / 141 operation (+3 endpoints mới: `POST /users/import`, `GET /users/import/template`, `DELETE /users/purge-test-users`; nâng cấp `DELETE /users/{user_id}` cho Admin; +3 schemas mới).

### 1. Endpoint mới & Cập nhật
- `POST /users/import`: Nhập danh sách quân nhân hàng loạt từ file Excel (`.xlsx`, `.xls`) hoặc Word (`.docx`), tự động ánh xạ đơn vị và vai trò biên chế quân sự.
- `GET /users/import/template`: Tải tệp tin mẫu định dạng chuẩn quân sự (Excel hoặc Word) có bảng định dạng sẵn.
- `DELETE /users/purge-test-users`: Dọn dẹp an toàn toàn bộ tài khoản thử nghiệm, chỉ bảo toàn tài khoản quản trị viên `admin` đang đăng nhập.
- `DELETE /users/{user_id}`: Nâng cấp cho phép Quản trị viên (Admin - role 0) có toàn quyền xoá bất kỳ tài khoản nào (kể cả tài khoản cấp Chỉ huy Lữ đoàn `role 1, 2, 3`), đồng thời tự động làm sạch các khoá ngoại liên kết an toàn mà không bị lỗi `IntegrityError`.

### 2. Schema mới
- `UserImportRowError`: `row_index: int`, `username: Optional[str]`, `error: str`.
- `UserImportResult`: `total_rows: int`, `success_count: int`, `error_count: int`, `errors: list[UserImportRowError]`, `created_usernames: list[str]`.
- `PurgeResult`: `purged_count: int`, `message: str`.

---

## v7.8.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Hệ thống Tin nhắn Tác chiến Nội bộ: Chat 1-1 trực tiếp & Chat nhóm kíp trực (Military Intranet Messaging System).
95 path / 138 operation (+8 endpoints mới, +6 schemas mới, +3 models: `chat_conversations`, `chat_participants`, `chat_messages`).

### 1. Endpoint mới
- `GET /chats`: Danh sách các cuộc trò chuyện tác chiến của quân nhân, tự động kèm số tin chưa đọc (`unread_count`) và tin nhắn gần nhất.
- `GET /chats/unread-count`: Tổng số tin nhắn chưa đọc toàn hệ thống của quân nhân (phục vụ huy hiệu đỏ trên Navbar).
- `POST /chats/direct`: Mở hoặc tìm kiếm cuộc trò chuyện 1-1 trực tiếp giữa 2 quân nhân (đảm bảo tính duy nhất, chặn tự chat).
- `POST /chats/group`: Tạo nhóm trao đổi nghiệp vụ / kíp trực tác chiến mới, tự động gán quyền admin cho người tạo.
- `GET /chats/{id}/messages`: Lấy lịch sử tin nhắn trong cuộc trò chuyện, tự động đánh dấu đã đọc (chặn 403 đối với người ngoài nhóm).
- `POST /chats/{id}/messages`: Gửi tin nhắn mới vào cuộc trò chuyện.
- `POST /chats/{id}/read`: Đánh dấu đã đọc toàn bộ tin nhắn trong cuộc trò chuyện.
- `POST /chats/{id}/members`: Thêm đồng chí vào nhóm chat.
- `DELETE /chats/{id}/members/{user_id}`: Rời nhóm hoặc quản trị viên xóa thành viên khỏi nhóm.

### 2. Schema mới
- `DirectChatCreate`: `recipient_id: int`.
- `GroupChatCreate`: `name: str`, `member_ids: List[int]`.
- `ChatMessageCreate`: `content: str`, `attachment_url: Optional[str]`, `attachment_name: Optional[str]`.
- `ChatMessageOut`: Thông tin người gửi, cấp bậc, chức vụ, nội dung, cờ `is_me`, dấu thời gian.
- `ChatConversationOut`: Thông tin cuộc trò chuyện, loại chat, tên người đối thoại / tên nhóm, `unread_count`, danh sách thành viên.
- `ChatAddMemberPayload`: `user_id: int`.
- `ChatUnreadCountResponse`: `total_unread: int`.

---

## v7.7.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Bàn làm việc Chỉ đạo của Ban Chỉ huy Lữ đoàn & Phân định giao việc theo chức danh (Leadership Tasks & Command Directives).
87 path / 129 operation (+5 endpoints mới, +5 schemas mới, +1 model bảng `leadership_tasks`, +1 service & repository).

### 1. Endpoint mới
- `GET /leadership-tasks`: Danh sách và tra cứu các chỉ đạo, giao việc của Ban Chỉ huy Lữ đoàn. Hỗ trợ bộ lọc đa tiêu chí: `commander_role`, `target_branch`, `assigned_unit_id`, `status`, `urgency`, phân trang (`skip`, `limit`).
- `GET /leadership-tasks/{id}`: Xem chi tiết một chỉ đạo tác chiến / nhiệm vụ giao của Chỉ huy Lữ đoàn.
- `POST /leadership-tasks`: Ban Chỉ huy Lữ đoàn ban hành Chỉ đạo, Mệnh lệnh, Giao việc mới (Yêu cầu `role <= 2`).
- `POST /leadership-tasks/{id}/report`: Đơn vị cơ sở hoặc trợ lý ban ngành báo cáo tiến độ, kết quả thực hiện chỉ đạo.
- `POST /leadership-tasks/{id}/review`: Ban Chỉ huy Lữ đoàn đánh giá kết quả, bút phê chỉ đạo bổ sung hoặc kết luận hoàn thành (Yêu cầu `role <= 2`).

### 2. Schema mới
- `LeadershipTaskCreate`: Dữ liệu ban hành chỉ đạo (`commander_role`, `title`, `content`, `target_branch`, `assigned_unit_id`, `urgency`, `deadline`).
- `LeadershipTaskReport`: Báo cáo kết quả thực hiện của đơn vị (`report_content`).
- `LeadershipTaskReview`: Đánh giá và bút phê của Ban Chỉ huy (`status`, `review_note`).
- `LeadershipTaskOut`: Dữ liệu chi tiết chỉ đạo, bao gồm nhãn tiếng Việt cho chức vụ chỉ huy, khối ngành, độ khẩn, trạng thái và dấu thời gian.
- `LeadershipTaskListResponse`: Cấu trúc phân trang danh sách chỉ đạo (`items: List[LeadershipTaskOut]`, `total: int`).

### 3. Phân định chức danh Ban Chỉ huy Lữ đoàn
- `lu_truong`: Lữ đoàn trưởng — Phụ trách Quân sự, Tác chiến, Kế hoạch SSCĐ, chỉ đạo Phòng Tham mưu và toàn đơn vị.
- `chinh_uy`: Chính uỷ Lữ đoàn — Phụ trách CTĐ-CTCT, Tuyên huấn, Cán bộ, Cấp uỷ, chỉ đạo Phòng Chính trị.
- `lu_pho_tmt`: Phó Lữ đoàn trưởng kiêm TMT — Phụ trách Tác chiến, Huấn luyện chiến đấu, Hệ thống TTLL cơ động, điều hành Phòng Tham mưu, d1, d2.
- `lu_pho_hckt`: Phó Lữ đoàn trưởng HC-KT — Phụ trách Vũ khí trang bị, Khí tài TTLL, Hậu cần - Kỹ thuật, điều hành Phòng Hậu cần - KT, c5, Trạm TTLL.
- `pho_chinh_uy`: Phó Chính uỷ Lữ đoàn — Phụ trách Công tác quần chúng, Dân vận, Chính sách quân đội.

---

## v7.6.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Phân quyền đa cấp theo Khối/Ngành (Tham mưu, Chính trị, Hậu cần – Kỹ thuật) & Ma trận quyền hạn quân sự (Branch-scoped RBAC Matrix).
83 path / 124 operation (+1 endpoint mới, +1 schema mới, +1 module core rbac).

### 1. Endpoint mới
- `GET /profile/permissions`: Trả về toàn bộ ma trận phân quyền thực tế của quân nhân đang đăng nhập, bao gồm: vai trò (`role`, `role_label`), Khối/Ngành chức năng (`branch`, `branch_label`), đơn vị (`unit_id`, `unit_name`), và danh sách các quyền hạn chi tiết (`permissions`: quản lý Tham mưu, Chính trị, Hậu cần - KT, duyệt kíp trực, xuất bản tin tức, xem nhật ký bảo mật...).

### 2. Schema mới
- `UserPermissionsOut`: Cấu trúc dữ liệu trả về thông tin phân quyền và ma trận quyền hạn chi tiết của quân nhân.

### 3. Quy chuẩn Khối/Ngành quân sự
- **Khối Tham mưu (`tham_muu`):** Phụ trách Tác chiến, Canh trực SSCĐ, Quản lý kíp trực, Mạng thông tin liên lạc, Công văn chỉ thị.
- **Khối Chính trị (`chinh_tri`):** Phụ trách CTĐ-CTCT, Tuyên huấn, Bản tin nội bộ, Tư liệu Giáo dục chính trị & Lịch sử truyền thống, Bảo vệ an ninh.
- **Khối Hậu cần – Kỹ thuật (`hau_can_ky_thuat`):** Phụ trách Bảo đảm vũ khí trang bị, Khí tài TTLL, Xe máy kỹ thuật, Quân y, Doanh trại.
- **Toàn Lữ đoàn (`toan_lu_doan`):** Ban Chỉ huy Lữ đoàn (`role 1, 2`) và Quản trị hệ thống (`role 0`) có toàn quyền chỉ đạo và điều hành trên mọi khối ngành.
- **Đơn vị cơ sở (`don_vi_co_so`):** Tiểu đoàn, Đại đội, Trạm thực hiện nhiệm vụ theo thẩm quyền cấp cơ sở.

---

## v7.5.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Biên bản bàn giao ca trực & Sổ nhật ký kíp trực điện tử (Shift Handover & Electronic Duty Log).
82 path / 123 operation (+4 endpoint mới, +5 schema mới, +1 model mới).

### 1. Endpoint mới
- `GET /duty-shift-handovers`: Danh sách Sổ bàn giao ca trực và Nhật ký kíp trực (hỗ trợ lọc theo ngày, đơn vị, trạng thái: `cho_nhan`, `da_nhan`, `co_kien_nghi`).
- `GET /duty-shift-handovers/by-schedule/{schedule_id}`: Lấy biên bản bàn giao gắn với một dòng ca trực cụ thể.
- `POST /duty-shift-handovers`: Lập biên bản bàn giao ca trực (báo cáo quân số, vũ khí khí tài, sự vụ trong ca, nhiệm vụ tồn đọng).
- `POST /duty-shift-handovers/{id}/acknowledge`: Ca sau ký nhận bàn giao, xác nhận hiện trạng vũ khí trang bị và ghi chú nhận ca.
- `POST /duty-shift-handovers/{id}/review`: Chỉ huy đơn vị kiểm tra, phê duyệt và ghi ý kiến chỉ đạo kíp trực.

### 2. Schema mới
- `DutyShiftHandoverCreate`: Dữ liệu lập biên bản (schedule_id, receiver_id, receiver_name, giver_name, personnel_report, equipment_status, incident_log, pending_tasks).
- `DutyShiftHandoverAcknowledge`: Dữ liệu ký nhận ca (receiver_note, status: `da_nhan` | `co_kien_nghi`).
- `DutyShiftHandoverCommanderReview`: Dữ liệu phê duyệt của Chỉ huy (commander_note).
- `DutyShiftHandoverOut`: Chi tiết biên bản bàn giao đầy đủ (kèm thông tin ca trực, đơn vị, người giao, người nhận, thời gian ký nhận).
- `DutyShiftHandoverListResponse`: Cấu trúc phân trang danh sách biên bản (`items`, `total`).

### 3. Quy tắc nghiệp vụ & Bảo mật
- **RBAC:** Mọi cán bộ trực ca đều có thể lập và ký nhận biên bản; Chỉ cán bộ Chỉ huy (`role <= 3`) mới có quyền ghi ý kiến chỉ đạo phê duyệt vào sổ nhật ký kíp trực.
- **Tính toàn vẹn & Chống ghi đè:** Mỗi ca trực chỉ cho phép tạo duy nhất 1 biên bản bàn giao; hệ thống chặn tạo trùng lặp (HTTP 400).
- **Audit Trail:** Tự động ghi nhận các sự kiện `DUTY_HANDOVER_CREATED`, `DUTY_HANDOVER_ACKNOWLEDGED`, `DUTY_HANDOVER_REVIEWED` vào Nhật ký an ninh hệ thống.

---

## v7.4.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Kiểm soát an toàn tệp tải lên (File Upload Security, Magic Bytes Validation & Quota Enforcement).
78 path / 118 operation (giữ nguyên số endpoint, nâng cấp logic xác thực tệp tầng core uploads).

### Cơ chế bảo vệ mới
- **Kiểm tra chữ ký nhị phân thực tế (Magic Bytes):** Đối chiếu chữ ký nhị phân các file ảnh (`PNG`, `JPEG`, `GIF`, `WebP`), tài liệu (`PDF`, `DOC`, `DOCX`, `XLS`, `XLSX`, `PPT`, `PPTX`) và video (`MP4`, `MOV`, `WebM`, `OGG`). Chặn đứng hành vi đổi đuôi tệp giả mạo (Extension Spoofing).
- **Chặn đứng mã độc & Web Shell:** Quét và từ chối các tệp chứa header thực thi Windows PE (`MZ`), Linux ELF (`\x7fELF`), bytecode Java Class (`\xca\xfe\xba\xbe`), các script PHP, shell script, JSP, HTML nhúng ngầm.
- **Làm sạch tên tệp & Chống Path Traversal:** Loại bỏ toàn bộ tiền tố đường dẫn nguy hiểm (`../`, `..\\`), ký tự null byte và ký tự điều khiển trong tên file.
- **Kiểm soát dung lượng lưu trữ an toàn (Disk Quota Guard):** Kiểm tra dung lượng ổ đĩa khả dụng (`MIN_FREE_DISK_MB = 500`), từ chối lưu file nếu ổ đĩa máy chủ còn dưới 500MB để chống cạn kiệt tài nguyên hệ thống.

---

## v7.3.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Giới hạn tần suất yêu cầu & Chống dò quét mật khẩu (Rate Limiting & Brute-force Protection).
78 path / 118 operation (giữ nguyên số endpoint, bổ sung cơ chế bảo vệ tầng giao vận và xác thực).

### Cơ chế bảo vệ mới
- **Chống Brute-force đăng nhập (`POST /users/login`):** Tự động theo dõi số lần đăng nhập thất bại theo IP và Username. Nếu nhập sai quá 5 lần trong 5 phút $\rightarrow$ khóa tạm thời 15 phút, trả về HTTP 429 Too Many Requests kèm header `Retry-After`. Tự động ghi nhật ký an ninh `LOGIN_LOCKOUT_TRIGGERED` và `LOGIN_BLOCKED_BRUTE_FORCE` vào bảng `audit_logs`.
- **Giới hạn lưu lượng theo IP (`SlidingWindowRateLimiter`):** Bảo vệ các endpoint API trước các đợt flood request từ máy trạm LAN (ngưỡng mặc định 120 req/phút), đính kèm header `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`. Không áp dụng giới hạn đối với tài nguyên tĩnh.

---

## v7.2.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Nhật ký kiểm toán an ninh mạng (Audit Trail). Ghi nhận và truy vết các hành động trọng yếu (đăng nhập/thất bại, thay đổi quyền/vai trò/cơ mật, tải công văn mật, đóng/mở tài khoản). Bổ sung endpoint tra cứu nhật ký an ninh cho Ban Chỉ huy và Quản trị.
78 path / 118 operation (tăng 1 path / 1 operation).

### Thêm / Sửa / Xoá endpoint
- `GET /audit-logs` — Lấy danh sách nhật ký an ninh hệ thống có phân trang (`page`, `page_size`), lọc theo `action`, `actor_id`, `target_type`, `is_success`, khoảng thời gian `from_date`/`to_date`, và tìm kiếm từ khoá `search`. Phân quyền nghiêm ngặt: chỉ Ban Chỉ huy (role 0, 1, 2) và Admin mới được phép truy xuất (các role khác nhận 403 Forbidden).

### Schema mới
- `AuditLogOut` — Dữ liệu chi tiết một bản ghi nhật ký kiểm toán (id, actor_id, actor_username, actor_full_name, actor_role, action, target_type, target_id, target_name, ip_address, is_success, details, created_at).
- `AuditLogListResponse` — Kết quả phân trang danh sách nhật ký kiểm toán (`items: AuditLogOut[]`, `total: int`, `page: int`, `page_size: int`).

### Nghiệp vụ tự động ghi log bảo mật (Audit Hook)
- Đăng nhập thành công / Thất bại (kèm IP client).
- Khóa / Kích hoạt tài khoản người dùng.
- Thay đổi vai trò (role) / Quyền cơ mật (clearance) / Phân quyền kênh chỉ đạo, kênh chỉ huy.
- Đặt lại mật khẩu người dùng bởi quản trị.
- Tải tệp công văn mật (DISPATCH_DOWNLOAD) kèm định danh công văn và người tải.

---

## v7.1.0 — 2026-09-06

**Người bàn giao:** Backend
**Phạm vi:** Bảo mật tệp đính kèm MẬT (công văn mật, tài liệu luồng mật BCH & Cấp uỷ). Thêm endpoint download tệp đính kèm tin nhắn.
77 path / 117 operation (tăng 1 path / 1 operation).

### Thêm / Sửa / Xoá endpoint
- `GET /command-threads/{thread_id}/messages/{message_id}/download` — Tải tệp đính kèm tin nhắn trong luồng trao đổi mật BCH & Cấp uỷ có kiểm tra xác thực và quyền xem mật.
- `POST /official-dispatches` và `PUT /official-dispatches/{id}` — Tệp đính kèm công văn mật được lưu trữ bảo mật tại `storage/secure_uploads/dispatches/`, cách ly hoàn toàn khỏi `/static/`.
- `POST /command-threads/{id}/documents` — Tệp văn bản chia sẻ trong luồng mật được lưu tại `storage/secure_uploads/command_docs/`, cách ly hoàn toàn khỏi `/static/`.
- `POST /command-threads/{id}/messages` — Tệp đính kèm tin nhắn luồng mật được lưu tại `storage/secure_uploads/command_messages/`, cách ly hoàn toàn khỏi `/static/`.
- `GET /official-dispatches/{id}/download` và `GET /command-threads/{thread_id}/documents/{doc_id}/download` — Tự động phân giải tệp từ kho bảo mật `secure_upload_path`, có cơ chế fallback tương thích ngược cho các tệp cũ trong `upload_path`.

### Thay đổi schema
- Không thay đổi các trường dữ liệu hiện tại, hoàn toàn tương thích ngược với client cũ.
- Tăng `API_VERSION` lên `7.1.0`.

### Ảnh hưởng Frontend
- Cập nhật `fe-ludoan/src/api/commandDispatches.ts` bổ sung phương thức `downloadMessageAttachment` để tải tệp đính kèm tin nhắn qua endpoint an toàn có kèm JWT token.
- Cập nhật `KenhChiHuyPage.tsx` chuyển link tải tệp đính kèm tin nhắn từ `fileUrl(attachment_url)` sang hàm tải an toàn `downloadMessageAttachment`.

### Kiểm thử đã thực hiện
- `backend/scripts/test_secure_dispatch_storage.py` (100% PASS): Xác nhận tệp mật không bị lộ qua `/static/`, chỉ người có quyền xem MẬT mới tải được tệp, cơ chế xóa tệp an toàn và tương thích ngược file cũ.
- `backend/scripts/test_post_rbac.py` (100% PASS): Các phân hệ nội dung và phân quyền không bị ảnh hưởng.

---

## v7.0.0 — 2026-09-03

**Người bàn giao:** Backend
**Phạm vi:** Gỡ bỏ hoàn toàn tính năng **Giao ban trực tuyến / Cuộc họp Ban Chỉ
huy & Cấp uỷ** (`command_meetings`). Xoá endpoint → **MAJOR**.
76 path / 116 operation (trước: 83 path / 127 operation — giảm 7 path / 11 operation).

### Thêm / Sửa / Xoá endpoint
Xoá toàn bộ router `command-meetings` (prefix `/command-meetings`):
- `GET /command-meetings` — danh sách cuộc họp.
- `POST /command-meetings` — tạo cuộc họp.
- `GET /command-meetings/{meeting_id}` — chi tiết.
- `PUT /command-meetings/{meeting_id}` — cập nhật.
- `DELETE /command-meetings/{meeting_id}` — xoá.
- `POST /command-meetings/{meeting_id}/minutes` — ghi biên bản kết luận.
- `POST /command-meetings/{meeting_id}/attachment` — tải tài liệu họp lên.
- `GET /command-meetings/{meeting_id}/download` — tải tài liệu họp.
- `POST /command-meetings/{meeting_id}/attendees` — mời thành phần triệu tập.
- `DELETE /command-meetings/{meeting_id}/attendees/{user_id}` — gỡ thành phần.
- `PATCH /command-meetings/{meeting_id}/attendees/{user_id}` — cập nhật điểm
  danh / lý do vắng / ý kiến đóng góp.

### Thay đổi schema
Xoá các schema: `CommandMeetingCreate`, `CommandMeetingUpdate`,
`CommandMeetingOut`, `CommandMeetingDetailOut`, `AttendeeOut`, `AttendanceUpdate`,
`InviteRequest`, `MinutesRequest`, `Body_upload_attachment_command_meetings__meeting_id__attachment_post`.
Các schema/enum khác không đổi. `has_secret_clearance`, `can_access_command_channel`,
`is_command_level` (ở `app/core/access.py`) vẫn giữ — còn dùng cho Kênh chuyên
BCH (`command-threads`, `official-dispatches`).

### Ảnh hưởng cơ sở dữ liệu
Model `command_meeting` không còn được đăng ký; `Base.metadata.create_all`
không đụng tới bảng cũ. Hai bảng `command_meetings` và
`command_meeting_attendees` (nếu DB đã tạo) trở thành bảng chết — có thể xoá tay
bằng `scripts/drop_command_meetings.py` (idempotent) khi thuận tiện.

### Ảnh hưởng Frontend
- Xoá: `src/pages/GiaoBanTrucTuyenPage.tsx`, `src/api/commandMeetings.ts`,
  `src/types/commandMeeting.ts`, `src/config/meetingPresets.ts`,
  `src/components/DevicePreCheck.tsx`.
- `src/App.tsx`: gỡ route `/giao-ban` + import.
- `src/config/unit.ts`: gỡ mục menu "Giao ban trực tuyến" trong nhóm "Kênh chỉ
  huy (MẬT)" (nhóm còn 1 mục: "Trao đổi – Công văn").
- `src/App.css`: gỡ block CSS "Giao ban truc tuyen — hinh thuc hop + kiem tra
  thiet bi"; block "danh sach + phan trang" giữ lại (dùng chung với
  `Pagination.tsx`), chỉ bỏ tiền tố `.meeting-*`.
- `src/pages/HuongDanPage.tsx`: bỏ các dòng nhắc tới "Giao ban trực tuyến".
- Xem chi tiết: `docs-backend/SYNC_REQUEST_remove-giao-ban.yaml`.

### Kiểm thử đã thực hiện
- `from app.main import app` import sạch; `app.version == "7.0.0"`;
  `Base.metadata.create_all` chạy không lỗi.
- `scripts/export_openapi.py` → `Da xuat phien ban 7.0.0: 76 path / 116 operation`.
- `grep "command-meeting\|CommandMeeting" openapi.yaml` → 0 kết quả.
- `scripts/test_full_system.py`: gỡ PHASE 5 (Giao ban) + câu lệnh dọn DB
  `command_meeting*`; còn 4 PHASE.

---

## v6.4.0 — 2026-09-03

**Người bàn giao:** Backend
**Phạm vi:** Văn bản – Tài liệu – Biểu mẫu (`documents`) — cho phép thay tệp
đính kèm khi sửa tài liệu.
Thêm field optional, không phá vỡ client cũ → **MINOR**.
83 path / 127 operation (không đổi số lượng).

### Thêm / Sửa / Xoá endpoint
- `PUT /documents/{doc_id}` — bổ sung field `file` (multipart, optional) vào
  request body. Quyền: `DOCUMENT_MANAGE_ROLES` (`role ∈ {0,1,2}`) như cũ.
  - Không gửi `file` (hoặc gửi rỗng) → chỉ cập nhật metadata, tệp gốc giữ nguyên
    (hành vi cũ, tương thích ngược).
  - Gửi `file` hợp lệ (.pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx, ≤ `MAX_UPLOAD_MB`)
    → lưu tệp mới, cập nhật `file_url`/`file_name`/`file_size`/`content_type`,
    xoá tệp cũ trên đĩa sau khi lưu thành công.
  - Sai định dạng / vượt dung lượng / tệp rỗng → 400 (từ `save_upload`).

### Thay đổi schema
- `Body_update_document_documents__doc_id__put`: thêm `file?: binary | null`.
- `DocumentOut`: không đổi (các trường `file_*` nay có thể thay đổi giá trị sau
  khi sửa).

### Ảnh hưởng Frontend
- `frontend/src/api/documents.ts`: `update(id, data, file?)` — truyền tệp optional
  qua `toForm`.
- `frontend/src/pages/DocumentFormPage.tsx` (route `/van-ban/:id/sua`): thêm ô
  chọn tệp (không bắt buộc) ở chế độ sửa, hiển thị tên tệp hiện tại.
- Không cần đổi `frontend/src/types/document.ts`.

### Kiểm thử đã thực hiện
- `from app.main import app` import sạch; `Base.metadata.create_all` chạy không lỗi.
- `scripts/export_openapi.py` → `Da xuat phien ban 6.4.0: 83 path / 127 operation`.
- Đối chiếu `openapi.yaml`: body `PUT /documents/{doc_id}` đã có `file` (anyOf
  string binary / null), `required: [title, category]` — `file` không bắt buộc.

---

## v6.3.0 — 2026-09-03

**Người bàn giao:** Backend
**Phạm vi:** Tin tức – Hoạt động đơn vị (`posts`) — nâng cấp thành trình soạn
thảo kiểu CMS (tóm tắt, slug SEO, thẻ từ khoá, lưu nháp).
Thêm field/endpoint mới, không phá vỡ client cũ → **MINOR**.
83 path / 127 operation (+1 operation: `POST /posts/{post_id}/submit`).

### Lý do
Trang "Tạo/Đăng bài viết" được dựng lại theo bố cục CMS 2 cột (nội dung 70% –
sidebar cài đặt 30%). Cần backend lưu thêm phần tóm tắt hiển thị ở thẻ tin, slug
rút gọn cho SEO, thẻ từ khoá, và một trạng thái "nháp" để lưu bài chưa gửi duyệt.
**Không** thêm `GET /api/categories` (danh mục `posts` là enum cố định — FE tự có
nhãn) và **không** thêm `/api/media/upload` (đã có sẵn `POST /api/upload` trả về
`{url}`, dùng luôn cho ảnh bìa + ảnh trong bài).

### Thêm / Sửa / Xoá endpoint
- `POST /posts/{post_id}/submit` — **mới**. Quyền: `CONTENT_ROLES` (role 0..4),
  chỉ tác giả hoặc chỉ huy. Chuyển bài từ `nhap` / `tra_lai` → `cho_duyet`
  (role 4) hoặc `da_duyet` (role ≤ 3). Trả **200** (`PostOut`). Chặn:
  - **409** — bài không ở trạng thái `nhap`/`tra_lai`.
  - **403** — không phải tác giả và không phải chỉ huy.
  - **404** — không tìm thấy / không được xem.
- `POST /posts` — **sửa**: thêm query `as_draft: bool = false`. `true` → tạo bài
  ở trạng thái `nhap` bất kể vai trò (không đẩy vào hàng duyệt).
- `PUT /posts/{post_id}` — **sửa**: thêm query `as_draft: bool = false`.
  `true` → giữ/đưa bài về `nhap`. Khi bài đang là `nhap` mà lưu với
  `as_draft=false` → coi như gửi duyệt (`cho_duyet` hoặc `da_duyet` nếu chỉ huy).
- `GET /posts?status_filter=` — nay chấp nhận thêm giá trị `nhap` (chỉ huy lọc).

### Thay đổi schema
- `PostCreate`: **thêm** `summary: str | null` (≤500), `slug: str | null` (≤255,
  để trống → backend tự sinh từ tiêu đề, bỏ dấu tiếng Việt, trùng thì thêm hậu tố
  `-2`, `-3`…), `tags: string[]` (mặc định `[]`, tối đa 20 thẻ, mỗi thẻ ≤40 ký
  tự, tự lược trùng/rỗng).
- `PostOut`: **thêm** `summary`, `slug`, `tags` (cùng kiểu như trên; `slug` luôn
  có giá trị sau khi tạo).
- `PostStatus`: **thêm** giá trị `nhap` → `['nhap','cho_duyet','da_duyet','tra_lai']`.
- Không đổi tên/kiểu field cũ nào.

### Thay đổi model / DB
- `posts`: thêm cột `summary VARCHAR(500) NULL`, `slug VARCHAR(255) NULL UNIQUE`
  (index `ux_posts_slug`), `tags JSON NOT NULL DEFAULT '[]'`.
- Migration thủ công (idempotent, không mất dữ liệu):
  `scripts/migrate_posts_cms.py` — ADD COLUMN + backfill `tags='[]'` + sinh
  `slug` từ tiêu đề cho các bài cũ + tạo unique index. **Đã chạy trên DB dev.**

### Ảnh hưởng Frontend
- `frontend/src/types/post.ts`: `Post` + `PostCreate` thêm `summary`, `slug`,
  `tags`; `PostStatus` thêm `'nhap'`; `POST_STATUS_LABELS` thêm nhãn "Bản nháp".
- `frontend/src/api/posts.ts`: `create`/`update` nhận thêm `asDraft?: boolean`
  (→ `?as_draft=true`); thêm `postsApi.submit(id)` → `POST /posts/{id}/submit`.
- `frontend/src/pages/PostsPage.tsx`: dựng lại form theo bố cục CMS 2 cột
  (tiêu đề borderless cỡ lớn + ô tóm tắt + editor | sidebar: Lưu nháp / Xem
  trước / Đăng bài, danh mục, bậc truy cập, nổi bật, dropzone ảnh bìa có
  preview, thẻ từ khoá, slug). Nút "Gửi duyệt" cho bài đang ở `nhap`.
- `frontend/src/components/RichContentEditor.tsx`: thêm H1/H2, danh sách có số,
  chèn liên kết, chèn bảng, nút trích dẫn (vẫn upload qua `POST /api/upload`).
- `frontend/src/App.css`: style bố cục CMS + bổ sung toolbar editor.
- Màn hình ảnh hưởng: `/tin-tuc` (PostsPage). Trang chủ / trang công khai chưa
  bắt buộc dùng `summary` (có thể dùng dần thay cho `excerptFromHtml`).

### Kiểm thử đã thực hiện
- `from app.main import app` import sạch; `app.openapi()` → 83 path / 127 operation.
- `scripts/test_post_rbac.py` (SQLite in-memory) — cập nhật sang role số (0..5);
  **18/18 PASS**, gồm 8 case mới cho luồng nháp/gửi-duyệt/slug:
  `draft-create-status = nhap`, `slug` tự sinh `ban-nhap-dau-tien`, trùng →
  `…-2`, bản nháp ẩn với người khác, `submit` (officer)→`cho_duyet`,
  `submit` lại →409, `submit` (chỉ huy)→`da_duyet`.
- `scripts/migrate_posts_cms.py` chạy trên DB dev: thêm 3 cột, backfill tags +
  slug, tạo `ux_posts_slug` OK.
- Runtime: `uvicorn app.main:app` → `GET /posts` 200; `/openapi.json` xác nhận
  `PostOut` có `summary/slug/tags`, `status` enum có `nhap`, có
  `POST /posts/{post_id}/submit`, query `as_draft` trên POST/PUT.
- `scripts/export_openapi.py` → `Da xuat phien ban 6.3.0: 83 path / 127 operation`.

## v6.2.0 — 2026-09-02

**Người bàn giao:** Backend
**Phạm vi:** Quản lý người dùng (`users`) — thêm endpoint xoá hẳn tài khoản.
Thêm endpoint mới, không phá vỡ client cũ → **MINOR**. 82 path / 126 operation
(+1 operation: `DELETE /users/{user_id}`).

### Lý do
Trang "Quản lý người dùng" cần nút Xoá để dọn các tài khoản tạo nhầm / tự đăng ký
rác chưa từng đăng nội dung. Trước đây chỉ có `deactivate` (khoá) chứ không xoá được.

### Thêm / Sửa / Xoá endpoint
- `DELETE /users/{user_id}` — **mới**. Quyền gọi: `USER_DELETE_ROLES` =
  `role ∈ {0, 1, 2}` (Quản trị hệ thống, Lữ trưởng - Chính uỷ, Lữ phó - Phó chính uỷ).
  Chỉ huy đơn vị (`role = 3`) truy cập được trang nhưng **không** gọi được (403).
  `role ≥ 4` → 403. Trả **204** khi thành công. Các nhánh chặn
  (ở `user_service.delete_user`):
  - **400** — tự xoá tài khoản của chính mình.
  - **409** — tài khoản hệ thống (`is_system`).
  - **409** — **tài khoản mục tiêu có `role ∈ {0, 1, 2}`** (`USER_UNDELETABLE_ROLES`):
    không xoá tài khoản cấp chỉ huy từ Lữ phó trở lên; phải hạ quyền
    (`PATCH /users/{id}/role`) rồi mới xoá, hoặc khoá tài khoản. Chỉ tài khoản
    `role ∈ {3, 4, 5}` mới xoá được.
  - **409** — là tài khoản chỉ huy (vai trò 0..3) đang hoạt động cuối cùng.
  - **409** — tài khoản đã gắn với nội dung / hoạt động đã đăng (khoá ngoại
    `IntegrityError`) → khuyến nghị dùng `POST /users/{id}/deactivate` để khoá.
  - **404** — không tìm thấy tài khoản.

### Thay đổi schema
- Không có. Không thêm/đổi schema nào.

### Ảnh hưởng Frontend
- `frontend/src/api/users.ts`: thêm `usersApi.remove(id)` → `DELETE /users/{id}`.
- `frontend/src/pages/UsersPage.tsx`: cột "Hành động" thêm nút icon thùng rác
  (`trash`), chỉ hiện khi người dùng hiện tại có `role ≤ 2` (`canDeleteUsers`);
  **disabled** với chính mình, tài khoản hệ thống, và **hàng có `u.role ≤ 2`**
  (không xoá được tài khoản cấp chỉ huy — tooltip nhắc hạ quyền / khoá). Bấm mở
  `useConfirm()` (modal cảnh báo, không dùng `window.confirm`) trước khi gọi API.
- Không cần đổi `frontend/src/types/user.ts` (không có schema mới).

### Kiểm thử đã thực hiện
- `from app.main import app` import sạch; `app.openapi()` → 82 path / 126 operation.
- `USER_DELETE_ROLES == (0, 1, 2)`, `USER_UNDELETABLE_ROLES == (0, 1, 2)`.
- Test guard `delete_user` (9 nhánh, mock repo): self→400, is_system→409,
  target role 0/1/2→409, chỉ huy đơn vị (role 3) cuối→409, happy-path role 3→None,
  happy-path role 5→None, IntegrityError→409. Tất cả PASS.
- `scripts/export_openapi.py` → `Da xuat phien ban 6.2.0: 82 path / 126 operation`.

## v6.0.0 — 2026-09-02

**Người bàn giao:** Backend
**Phạm vi:** Văn bản – Tài liệu – Biểu mẫu (`documents`) — siết quyền tạo/sửa/xoá.
Role `3` (Chỉ huy đơn vị) và `4` (Cá nhân) trước đây gọi được nay nhận **403** →
**đổi mã lỗi ⇒ MAJOR**. 82 path / 125 operation (giữ nguyên).

### Lý do
Yêu cầu nghiệp vụ: chỉ Quản trị hệ thống (`0`), Lữ trưởng/Chính uỷ (`1`),
Lữ phó/Phó chính uỷ (`2`) được quản lý kho Văn bản – Tài liệu. Các vai trò còn lại
chỉ được xem / tải về.

### Thêm / Sửa / Xoá endpoint
- `POST /documents` — quyền yêu cầu đổi từ `CONTENT_ROLES` (0..4) → `DOCUMENT_MANAGE_ROLES` (**0, 1, 2**). Role 3/4/5 → 403.
- `PUT /documents/{doc_id}` — như trên. Bỏ nhánh "tác giả tự sửa" (role 3/4 không còn sửa được kể cả tài liệu mình đăng).
- `DELETE /documents/{doc_id}` — như trên. Bỏ nhánh "tác giả tự xoá".
- `GET /documents`, `GET /documents/{doc_id}`, `GET /documents/{doc_id}/download` — **không đổi** (vẫn theo `classification` + `is_public`).

### Thay đổi schema
- Không có. `DocumentCreate` / `DocumentOut` giữ nguyên.

### Ảnh hưởng Frontend
- `frontend/src/pages/DocumentsPage.tsx`: nút "Tải lên / Sửa / Xoá" chỉ hiện khi `role <= 2` (thay `canEditContent`).
- `frontend/src/pages/DocumentFormPage.tsx`: chặn truy cập `/van-ban/moi` và `/van-ban/{id}/sua` khi `role > 2` (redirect về `/van-ban`).
- Không cần đổi `frontend/src/types/document.ts` hay `frontend/src/api/documents.ts` (hình dạng dữ liệu không đổi).

### Kiểm thử đã thực hiện
- `from app.main import app` import sạch.
- `can_manage_documents`: role 0/1/2 → True; role 3/4/5 → False.
- `scripts/export_openapi.py` → `Da xuat phien ban 6.0.0: 82 path / 125 operation`.

## v5.1.0 — 2026-09-02

**Người bàn giao:** Backend
**Phạm vi:** Xác thực — schema `Token` (response `POST /users/login`). Thêm field
mới, không phá vỡ client cũ → **MINOR**. 82 path / 125 operation (giữ nguyên).

### Lý do
Frontend cần biết vai trò tài khoản ngay tại bước đăng nhập mà không phải giải mã
JWT thủ công. `role` vốn đã có trong claim JWT (`role`), nay trả thêm ở thân
response cho tiện dùng.

### Thay đổi schema
- `Token`: **thêm** `role: integer` (bắt buộc), `enum: [0,1,2,3,4,5]` — vai trò
  của tài khoản vừa đăng nhập. Mô tả ghi rõ trong `openapi.yaml`:
  `0` = Quản trị hệ thống (admin) · `1` = Lữ trưởng - Chính uỷ ·
  `2` = Lữ phó - Phó chính uỷ · `3` = Chỉ huy các đơn vị ·
  `4` = Cá nhân · `5` = Người dùng (nguồn sự thật: `app/core/roles.py`).
  `access_token`, `token_type` giữ nguyên.

### Ảnh hưởng Frontend
- Cập nhật type `Token` trong `frontend/src/types/user.ts` (thêm `role: number`).
- `frontend/src/api/users.ts` `login()` trả về `Token` có thêm `role` — không bắt
  buộc dùng ngay (AuthContext vẫn đọc từ JWT), nhưng có thể dùng để bớt phụ thuộc
  giải mã token.
- Không có màn hình nào vỡ: field chỉ thêm vào.

### Kiểm thử đã thực hiện
- `from app.main import app` import sạch, không lỗi.
- `Token.model_json_schema()` → `required = ['access_token', 'role']`.
- `scripts/export_openapi.py` → `Da xuat phien ban 5.1.0: 82 path / 125 operation`.
- `openapi.yaml` schema `Token` đã có `role: integer`.

## v5.0.0 — 2026-09-02

**Người bàn giao:** Backend
**Phạm vi:** RBAC toàn hệ thống — `User.role` chuyển từ **chuỗi** (`"admin"` /
`"commander"` / `"officer"`) sang **số nguyên 0..5**. **Đổi kiểu field `role` +
đổi kiểu claim JWT `role` → MAJOR.** 82 path / 125 operation (giữ nguyên).

### Lý do
Đơn vị cần phân biệt rõ 6 cấp tài khoản theo chức trách thực tế thay vì gộp 3
nhóm. Số hoá vai trò để form tạo tài khoản chọn đúng cấp và để mở rộng về sau
(giới hạn theo đơn vị cho cấp 3).

### Bảng vai trò mới (`app/core/roles.py` — nguồn sự thật)
| role | Tên | Nhóm quyền (sơ đồ "A") |
|---|---|---|
| `0` | Quản trị hệ thống | Độc quyền admin **+** toàn quyền chỉ huy |
| `1` | Lữ trưởng – Chính uỷ | Toàn quyền chỉ huy (≈ `commander` cũ) |
| `2` | Lữ phó – Phó chính uỷ | Toàn quyền chỉ huy |
| `3` | Chỉ huy các đơn vị | Toàn quyền chỉ huy (chưa giới hạn theo đơn vị) |
| `4` | Cá nhân | Đăng/sửa Tin tức – Hoạt động + Giáo dục chính trị (≈ `officer` cũ) |
| `5` | Người dùng | Tài khoản đã kích hoạt, **chỉ xem** nội bộ, không đăng bài |

- `COMMAND_ROLES = (0,1,2,3)` thay cho mọi chỗ trước đây kiểm tra `role ==
  "commander"` / `role in ("commander","admin")` (ban hành Chỉ thị, duyệt/đăng mọi
  nội dung, quản lý tài khoản, vào kênh hạn chế, xem/tạo nội dung bậc `mat`).
- `CONTENT_ROLES = (0,1,2,3,4)` thay cho `require_roles("officer","commander")`.
- `ADMIN_ROLES = (0,)` thay cho `require_roles("admin")` (CRUD `/units`, cấp cờ
  kênh, reset mật khẩu, tạo admin khác).
- `has_secret_clearance` = `role ∈ {0,1,2,3}` **HOẶC** `User.clearance = True`
  (không đổi ngữ nghĩa, chỉ đổi cách tính cấp chỉ huy).

### Thay đổi schema
- `UserOut.role`: `string` → **`integer` (0..5)**. **Thêm** `UserOut.role_label:
  string` (tên hiển thị tiếng Việt của vai trò, ví dụ `"Lữ trưởng - Chính uỷ"`).
- `UserCreate.role`: `string` (default `"officer"`) → **`integer` enum
  `[0,1,2,3,4,5]`**, default **`4`** (Cá nhân). Sai giá trị → **422**.
- `RoleUpdate.role` (body `PATCH /users/{id}/role`): `enum
  ["officer","commander","admin"]` → **`integer` enum `[0,1,2,3,4,5]`**.
- `DirectiveAckUser.role`, `DispatchAckOut.role`: `string` → **`integer`**.

### Thay đổi hành vi endpoint (đường dẫn, method, status — KHÔNG đổi)
- `POST /users/register` — vai trò mặc định tài khoản tự đăng ký: `officer` →
  **`5` (Người dùng)**. Vẫn `is_active=false`, vẫn cần chỉ huy bổ sung rank +
  position + unit rồi `POST /users/{id}/activate`.
- `POST /users/` — `role` nhận số nguyên; chỉ tài khoản `role=0` mới tạo được
  tài khoản `role=0` khác (**403** nếu không).
- `PATCH /users/{id}/role` — body `{ "role": <0..5> }`. Vẫn: không tự hạ quyền
  chính mình khỏi nhóm `COMMAND_ROLES` (**400**); luôn giữ ≥ 1 tài khoản thuộc
  `COMMAND_ROLES` đang `is_active` (**409**); tài khoản `is_system` → **409**.
- `POST /users/login` — claim JWT `role` là **số nguyên** (không còn chuỗi); claim
  `adm` = `role == 0` (không đổi ý nghĩa). Các claim khác giữ nguyên.
- Toàn bộ endpoint đăng/sửa nội dung (`/posts`, `/education-materials`,
  `/announcements`, `/documents`, `/duty-schedules`, `/duty-week-plans`,
  `/api/upload`) — vai trò `5` không còn quyền ghi → **403**; `4` trở lên giữ
  nguyên như `officer`/`commander` cũ.

### Migration (BẮT BUỘC cho DB cũ — cột `role` đang là VARCHAR)
Chạy một lần, sau `scripts/migrate_rank_position.py`:

```
venv/Scripts/python.exe scripts/migrate_role_to_int.py
```

Idempotent (chạy lại khi cột đã là INT sẽ bỏ qua). Ánh xạ giá trị:
`admin→0`, `commander→1`, `officer→4`, `soldier` (legacy) `→5`, giá trị lạ `→5`;
rồi `ALTER TABLE users MODIFY COLUMN role INT NOT NULL DEFAULT 5`.
**Lưu ý:** mọi `commander` cũ về mức `1`; chỉ huy/admin chỉnh lại mức `2`/`3`
cho đúng chức trách qua `PATCH /users/{id}/role`.

### Ảnh hưởng Frontend (chưa làm trong đợt này — phạm vi chỉ Backend + hợp đồng)
- `frontend/src/types/user.ts`: `role` → `0 | 1 | 2 | 3 | 4 | 5`; thêm
  `role_label: string`. Bỏ union chuỗi `"officer" | "commander" | "admin"`.
- `AuthContext`: `role` là số; `isAdmin = role === 0`;
  `isCommander = role <= 3`; `canPostContent = role <= 4`;
  `canCommandChannel = hasClearance || role <= 3`. Claim `role` trong JWT nay là số.
- Form tạo/sửa người dùng (`UsersPage.tsx`): dropdown 6 vai trò 0..5 (nhãn lấy
  từ `role_label` hoặc map cứng); form đăng ký công khai không chọn vai trò.
- Mọi so sánh `role === 'commander'` / `'officer'` / `'admin'` trên UI phải đổi
  sang so sánh số theo bảng trên.
- Màn hình bị ảnh hưởng: đăng nhập, Quản lý người dùng, Hồ sơ, và mọi nút
  đăng/sửa/duyệt nội dung (ẩn/hiện theo vai trò số).

### Kiểm thử đã thực hiện
- `python -c "from app.main import app"` import sạch; `create_all` chạy sạch;
  `scripts/migrate_role_to_int.py` chạy trên DB thật: `admin→0`, tài khoản
  `officer` hiện có `→4`, cột đổi sang INT.
- Runtime (`uvicorn` cổng 8000):
  - `POST /users/login` (admin) → 200, JWT `role=0` (số), `adm=true`.
  - `GET /users/` (role 0) → 200, mỗi item có `role` (số) + `role_label`.
  - `POST /users/` `role=3` → 201; `role=9` → **422**.
  - `PATCH /users/{id}/role` `{ "role": 1 }` → 200, `role_label="Lữ trưởng - Chính uỷ"`.
  - `POST /posts` bằng tài khoản `role=5` → **403**; `POST /directives` bằng
    `role=3` → **201**; `POST /directives` bằng `role=5` → **403**;
    `GET /posts` khách → **200**.
  - Dữ liệu test đã dọn, DB trở lại 2 tài khoản gốc.

## v4.3.0 — 2026-09-02

**Người bàn giao:** Backend
**Phạm vi:** `official_dispatches` (Kênh chỉ huy → Sổ công văn). Nâng thành **Sổ
đăng ký văn bản đi – đến** phục vụ nghiệp vụ văn thư: phân loại văn bản (điện mật,
chỉ thị, quyết định…), độ mật, độ khẩn, người ký, hạn xử lý, số tờ, số hồ sơ lưu
trữ. **Chỉ thêm trường (đều có mặc định) + 1 tham số lọc → MINOR**, không phá vỡ
client cũ. 82 path / 125 operation (giữ nguyên).

### Lý do
Sổ công văn cũ chỉ ghi được công văn đi/đến chung chung; đơn vị cần vào sổ theo
đúng thể loại văn bản quân sự/hành chính (điện mật, chỉ thị, quyết định, mệnh
lệnh, kế hoạch, báo cáo, tờ trình…) kèm độ mật – độ khẩn – người ký như một sổ
văn thư lưu trữ thực thụ.

### Thay đổi model (bảng `official_dispatches` — thêm cột, KHÔNG đổi/bỏ cột cũ)
- `doc_type` VARCHAR(20) NOT NULL DEFAULT `'cong_van'` — loại văn bản.
- `security_level` VARCHAR(20) NOT NULL DEFAULT `'mat'` — độ mật.
- `urgency` VARCHAR(20) NOT NULL DEFAULT `'thuong'` — độ khẩn.
- `signer` VARCHAR(200) NULL — người ký (chức vụ + họ tên).
- `deadline` DATE NULL — hạn xử lý / hạn trả lời.
- `page_count` INT NULL — số tờ.
- `archive_ref` VARCHAR(120) NULL — số hồ sơ lưu trữ (hộp/cặp).

### Enum mới (dùng trong `DispatchUpdate` / `OfficialDispatchOut` / query)
- `DocType`: `cong_van` · `dien_mat` · `chi_thi` · `quyet_dinh` · `menh_lenh` ·
  `thong_bao` · `thong_tri` · `ke_hoach` · `bao_cao` · `to_trinh` · `bien_ban` ·
  `huong_dan` · `giay_moi` · `khac`.
- `SecurityLevel`: `thuong` · `mat` · `toi_mat` · `tuyet_mat`.
- `Urgency`: `thuong` · `khan` · `thuong_khan` · `hoa_toc`.

### Sửa endpoint
- `POST /official-dispatches` và `PUT /official-dispatches/{id}` (multipart) —
  **thêm field form** (đều tuỳ chọn, có mặc định): `doc_type`, `security_level`,
  `urgency`, `signer`, `issued_date` (đã có), `deadline`, `page_count`,
  `archive_ref`. Client cũ không gửi các field này vẫn tạo được → mặc định
  `cong_van` / `mat` / `thuong`. Sai giá trị enum → **422**. Trùng
  `(direction, dispatch_number)` → **409**. Chỉ `commander`/`admin` vào sổ / sửa /
  xoá → **403** nếu không đủ quyền; thiếu quyền MẬT → **403**.
- `GET /official-dispatches` — **thêm query `doc_type`** (lọc theo loại văn bản),
  bên cạnh `direction`, `status_filter` như cũ.
- `OfficialDispatchOut` / `OfficialDispatchDetailOut` — thêm các field tương ứng
  (`doc_type`, `security_level`, `urgency`, `signer`, `deadline`, `page_count`,
  `archive_ref`); các field cũ giữ nguyên tên/kiểu.

### Migration
- DB cũ đã có bảng `official_dispatches`: chạy một lần
  `venv/Scripts/python.exe scripts/migrate_dispatch_doc_type.py` (idempotent) để
  thêm 7 cột. Bản ghi cũ → `doc_type='cong_van'`, `security_level='mat'`,
  `urgency='thuong'`, các cột còn lại NULL.

### Ảnh hưởng Frontend
- `frontend/src/types/commandDispatch.ts`: thêm `DocType` / `SecurityLevel` /
  `Urgency` + bảng nhãn; mở rộng `OfficialDispatch`, `OfficialDispatchDetail`,
  `DispatchFormValues`.
- `frontend/src/api/commandDispatches.ts`: `dispatchForm()` gửi thêm field; `list()`
  thêm tham số `doc_type`.
- `DispatchFormPage.tsx`: thêm ô Loại văn bản (đầu form), Độ mật, Độ khẩn, Người
  ký, Hạn xử lý, Số tờ, Số hồ sơ lưu trữ.
- `KenhChiHuyPage.tsx` (tab Sổ công văn): hiển thị chip loại văn bản + độ mật/độ
  khẩn ở danh sách và phần chi tiết; thêm bộ lọc theo loại văn bản; tìm kiếm khớp
  cả người ký.

### Kiểm thử đã thực hiện
- `app.openapi()` import sạch; version 4.3.0; 82 path / 125 operation (không đổi).
- Migration MySQL: thêm đủ 7 cột; chạy lại → "đã đầy đủ" (idempotent).
- Logic (service): tạo `dien_mat` (độ mật `toi_mat`, khẩn `hoa_toc`, người ký,
  hạn, số tờ, hồ sơ) → round-trip đúng; sửa sang `chi_thi` OK; lọc
  `doc_type=chi_thi` đúng; `doc_type` sai → `ValidationError` (422).
- Runtime API (multipart): tạo đầy đủ field → **201**; tạo **không** gửi
  `doc_type`/`security_level`/`urgency` (client cũ) → **201** với mặc định
  `cong_van`/`mat`/`thuong`; `GET ?doc_type=dien_mat` lọc đúng.

## v4.2.0 — 2026-09-02

**Người bàn giao:** Backend
**Phạm vi:** `posts` — mở rộng danh mục thể loại Tin tức – Hoạt động đơn vị.
Không đổi path/model/bảng (`posts.category` vẫn là `VARCHAR(50)`), chỉ thêm giá
trị hợp lệ cho enum `PostCategory` → **thêm giá trị, không phá vỡ client cũ** →
MINOR. 82 path / 125 operation (giữ nguyên).

### Lý do
4 thể loại cũ (`huan_luyen`, `dan_van`, `khen_thuong`, `guong_nguoi_tot`) chưa đủ
để cán bộ phân loại đúng mục khi đăng bài lên Bảng tin. Bổ sung 4 nhóm theo yêu
cầu đơn vị.

### Thay đổi schema
- `PostCategory` (enum dùng trong `PostCreate.category`, `PostOut.category`,
  query `GET /posts?category=`) **thêm 4 giá trị**:
  - `hoat_dong_don_vi` — Hoạt động đơn vị
  - `cong_tac_dang` — Công tác Đảng – công tác chính trị
  - `thong_tin_lien_lac` — Thông tin liên lạc – chuyên môn
  - `su_kien_le_ky_niem` — Sự kiện – Lễ, kỷ niệm
  Giá trị cũ giữ nguyên; bài đã đăng không bị ảnh hưởng.

### Ảnh hưởng Frontend
- `frontend/src/types/post.ts`: cập nhật union `PostCategory` + `POST_CATEGORY_LABELS`.
- Form đăng bài (`PostsPage`) + bộ lọc thể loại: tự có 8 lựa chọn.
- Giao diện danh sách bài kiểu "trang báo" áp cho `PostsPage` (/tin-tuc),
  khối tin mới trên `HomePage` (/bang-tin) và `EducationPage` (/giao-duc-chinh-tri)
  — thuần CSS/JSX, không đụng hợp đồng.

### Kiểm thử đã thực hiện
- `app.openapi()` import sạch; version 4.2.0; `PostCategory` = 8 giá trị; 82 path
  / 125 operation (không đổi).
- Logic (gọi thẳng service): tạo bài với cả 4 thể loại mới → OK; category không
  hợp lệ (`linh_tinh`) → `ValidationError` (422).
- `openapi.yaml` chứa enum mới (`su_kien_le_ky_niem`...).

## v4.1.0 — 2026-09-02

**Người bàn giao:** Backend
**Phạm vi:** `POST /api/upload` — cho phép **video** để chèn giữa bài Tin tức /
Giáo dục chính trị (soạn thảo kiểu trang báo: ảnh + video đúng vị trí trong nội
dung). Không đổi path/schema → **82 path / 125 operation** (giữ nguyên) → MINOR.

### Lý do
Trình soạn thảo nội dung (`RichContentEditor`) đã chèn được ảnh đúng vị trí con
trỏ, nhưng chèn **video thì báo lỗi** "Định dạng '.mp4' không được phép" vì
`POST /api/upload` chỉ nhận ảnh + tài liệu. Người dùng cần bài viết hiển thị đầy
đủ cả ảnh lẫn video.

### Sửa endpoint
- `POST /api/upload` — tập định dạng cho phép **thêm video**: `.mp4 .webm .ogg
  .mov .m4v` (ngoài ảnh `.jpg .jpeg .png .webp .gif` và tài liệu `.pdf .doc
  .docx .xls .xlsx .ppt .pptx` như cũ). Video dùng **giới hạn dung lượng riêng**
  `settings.MAX_VIDEO_UPLOAD_MB` (mặc định 200 MB), ảnh/tài liệu vẫn theo
  `settings.MAX_UPLOAD_MB`. Sai định dạng / vượt giới hạn / file rỗng → **400**;
  thiếu JWT → **401**; role không đủ → **403**. Thành công → **201** `UploadOut`
  (hình dạng không đổi: `{status, filename, url}`), file lưu
  `storage/uploads/common/<uuid>.<ext>`, phục vụ qua `/static/common/...`.

### Thay đổi cấu hình
- `.env` (đều có default, không bắt buộc khai báo): thêm `MAX_VIDEO_UPLOAD_MB`
  (mặc định 200).

### Thay đổi schema
- Không. `UploadOut` giữ nguyên.

### Ảnh hưởng Frontend
- `RichContentEditor`: thêm nút "Chèn video" (tải tệp .mp4/.webm/...) và "Nhúng
  video" (dán liên kết YouTube/Vimeo) — chèn `<video controls>` hoặc
  `<div class="rc-embed"><iframe>` đúng vị trí con trỏ; thêm nút Tiêu đề mục
  (`h3`) và Trích dẫn (`blockquote`).
- `utils/richContent.ts`: `sanitizeContentHtml` cho phép thêm thẻ `h2 figure
  figcaption video source iframe hr` + thuộc tính `controls type poster class
  allow allowfullscreen frameborder loading` ; hook DOMPurify chỉ giữ `<iframe>`
  có src thuộc YouTube/Vimeo, ép `<a>` mở tab mới an toàn.
- `RichContent` + CSS `.rich-content` / `.rich-editor-body`: video/iframe
  responsive (khung tỉ lệ 16:9), figure/figcaption, h2/h3, blockquote kiểu
  trang báo. Áp cho cả Tin tức (`PostsPage`) và Giáo dục chính trị
  (`EducationFormPage`/`EducationPage`).
- `frontend/src/api/uploads.ts`: cập nhật chú thích định dạng cho phép.

### Kiểm thử đã thực hiện
- `app.openapi()` import sạch; version 4.1.0; 82 path / 125 operation (không đổi).
- `.mp4 in ALLOWED_EXTENSIONS` = True, `.mov` = True, `.exe` = False.
- Runtime `POST /api/upload`: tệp `.mp4` → **201** (`url` `/static/common/*.mp4`);
  tệp `.exe` → **400** ("Định dạng '.exe' không được phép" — kèm danh sách mới có
  video).

## v4.0.0 — 2026-09-02

**Người bàn giao:** Backend
**Phạm vi:** Lịch trực – Kíp trực. Làm lại module thành **quy trình phê duyệt lịch
trực tuần theo từng đơn vị**: mỗi đơn vị lập *bảng trực tuần* (danh sách ca trực cả
tuần), trình → chỉ huy Lữ đoàn phê duyệt hàng tuần; bảng đã duyệt lên 2 màn tổng
hợp: (1) Kíp trực toàn Lữ đoàn theo ngày (gom theo đơn vị), (2) Trực tuần (7 ngày).
**Quy mô:** 82 path / 125 operation (từ 74/115 ở v3.1.0). **Có thay đổi phá vỡ** →
MAJOR: xoá `POST /duty-schedules`, đổi ngữ nghĩa `PUT/DELETE /duty-schedules/{id}`.

> Ghi chú: lần export này đồng bộ luôn phần drift đã tích luỹ của `openapi.yaml`
> (bản commit trước đứng ở v1.9.1). Mục changelog này chỉ mô tả delta module Lịch
> trực so với mốc v3.1.0.

### Lý do
Khối "Lịch trực kíp" cũ chỉ là một bảng phẳng thêm/xoá ca trực rời rạc, không gắn
đơn vị, không có luồng trình – duyệt. Người chỉ huy Lữ đoàn không nắm được từng đơn
vị đã lập/duyệt lịch trực tuần chưa, không bao quát được quân số từng vị trí trực
theo ngày / theo tuần. Bản này đưa về đúng nghiệp vụ: **báo cáo lịch trực tuần
được phê duyệt hàng tuần theo danh sách đơn vị**.

### Thực thể mới
- **`duty_week_plans`** (bảng trực tuần của một đơn vị): `unit_id` (FK `units`),
  `week_start` (luôn chuẩn hoá về Thứ Hai ISO), `status` (`nhap`/`cho_duyet`/
  `da_duyet`/`tra_lai` — giống luồng duyệt `posts`), `note`, `submitted_by_id`/
  `submitted_at`, `reviewed_by_id`/`reviewed_at`/`review_note`, `author_id`,
  `created_at`. **UNIQUE (`unit_id`, `week_start`)** — mỗi đơn vị 1 bảng/tuần.
- `duty_schedules` (dòng ca trực) **thêm** `week_plan_id` (FK `duty_week_plans`,
  nullable cho bản ghi cũ), `unit_id` (FK `units`, sao chép từ bảng cha),
  `duty_type` (`DutyType`, mặc định `khac`), `contact_phone`, `personnel_present`,
  `personnel_total`. Dòng ca trực chỉ thêm/sửa/xoá được khi bảng cha ở `nhap`/
  `tra_lai`; `da_duyet`/`cho_duyet` → **409** (phải `reopen`).

### Enum mới
- `DutyType` (7 nhóm cương vị cố định): `truc_chi_huy`, `truc_ban_tac_chien`,
  `truc_ban_noi_vu`, `truc_chuyen_mon`, `truc_ca_kip`, `truc_bao_ve`, `khac`.
- Trạng thái bảng trực tuần: `nhap` · `cho_duyet` · `da_duyet` · `tra_lai`.

### Thêm endpoint — `/duty-week-plans` (router `Depends(get_current_user)`)
- `POST /duty-week-plans` — `require_roles("officer","commander")`. Body
  `{unit_id, week_start, note?}`. `officer` bị ép `unit_id = User.unit_id` (chưa gán
  đơn vị → **400**); `commander`/`admin` chọn đơn vị bất kỳ (không tồn tại → **400**).
  `week_start` chuẩn hoá về Thứ Hai. Trùng (đơn vị, tuần) → **409**. Tạo xong
  `status=nhap`. → **201** `DutyWeekPlanOut`.
- `GET /duty-week-plans?unit_id=&week_of=&status_filter=` — `commander`/`admin` xem
  mọi đơn vị; `officer` xem bảng đơn vị mình (mọi trạng thái) + bảng `da_duyet` của
  đơn vị khác. → `DutyWeekPlanOut[]`.
- `GET /duty-week-plans/{plan_id}` — → `DutyWeekPlanDetail` (kèm `entries`). Ngoài
  phạm vi xem → **404**.
- `PUT /duty-week-plans/{plan_id}` — sửa `note`. Chỉ khi `nhap`/`tra_lai` + đúng
  đơn vị sở hữu (officer). Sai trạng thái → **409**, sai đơn vị → **403**.
- `DELETE /duty-week-plans/{plan_id}` — chỉ khi `nhap` (commander/admin bỏ qua ràng
  buộc này), đúng đơn vị. → **204**. Xoá bảng xoá luôn dòng ca trực (cascade).
- `POST /duty-week-plans/{plan_id}/entries` — thêm dòng ca trực vào bảng. Body =
  `DutyScheduleCreate` (`unit_id`/tuần suy từ bảng cha). Ngày ngoài tuần → **400**;
  bảng đã trình/duyệt → **409**. → **201** `DutyScheduleOut`.
- `POST /duty-week-plans/{plan_id}/submit` — đơn vị sở hữu trình duyệt.
  `nhap`/`tra_lai` → `cho_duyet` (đặt `submitted_by/at`, xoá thông tin duyệt cũ).
  Không ở `nhap`/`tra_lai` → **409**; chưa có dòng nào → **409**.
- `POST /duty-week-plans/{plan_id}/review` — **`require_roles("commander")`** (admin
  kế thừa). Body `{status: "da_duyet"|"tra_lai", review_note?}`. Chỉ khi
  `cho_duyet` → else **409**. Đặt `reviewed_by/at`, `review_note`.
- `POST /duty-week-plans/{plan_id}/reopen` — mở lại về `nhap`. `cho_duyet` → đơn vị
  sở hữu (rút lại) hoặc chỉ huy; `da_duyet` → **chỉ `commander`/`admin`** (else
  **403**); trạng thái khác → **409**.

### Thêm endpoint — bảng tổng hợp
- `GET /duty-schedules/board/day?day=YYYY-MM-DD[&unit_id=]` — Tính năng 1.
  `DutyDayBoard`: ca trực trong ngày **gom theo đơn vị**, mỗi nhóm kèm
  `plan_id`/`plan_status`/`plan_status_label` và cộng dồn `personnel_present`/
  `personnel_total`; kèm tổng toàn Lữ đoàn + `weekday_label`.
- `GET /duty-schedules/board/week?week_of=YYYY-MM-DD[&unit_id=]` — Tính năng 2.
  `week_of` chuẩn hoá về Thứ Hai; `DutyWeekBoard` gồm đúng 7 ngày (Thứ Hai → Chủ
  Nhật, mỗi ngày có `entries` + cộng dồn quân số + `is_today`), `week_label`, và
  **`unit_plans`** — ma trận trạng thái phê duyệt bảng trực tuần theo từng đơn vị.
- Cả 2 lọc hiển thị theo người xem: `commander`/`admin` thấy mọi trạng thái (kèm
  nhãn); `officer` thấy bảng `da_duyet` của đơn vị khác + mọi trạng thái của đơn vị
  mình; bản ghi cũ chưa gắn bảng tuần chỉ đơn vị sở hữu / chỉ huy thấy.

### Sửa / xoá endpoint (BREAKING so với v3.1.0)
- **Xoá** `POST /duty-schedules` — tạo ca trực nay đi qua
  `POST /duty-week-plans/{id}/entries`.
- `GET /duty-schedules` — thêm query `unit_id?`, `duty_type?`; kết quả lọc theo
  quyền xem; mỗi phần tử `DutyScheduleOut` thêm `week_plan_id`, `unit_id`,
  `unit_name`, `duty_type`, `duty_type_label`, `contact_phone`, `personnel_*`.
- `PUT /duty-schedules/{id}` / `DELETE /duty-schedules/{id}` — nay là **sửa/xoá một
  dòng ca trực trong bảng trực tuần**: dòng cũ không gắn bảng → **409**; sai đơn vị
  → **403**; bảng đã trình/duyệt → **409**; ngày ngoài tuần (PUT) → **400**.
- `GET /duty-schedules/{id}` — thêm ràng buộc quyền xem (ngoài phạm vi → **404**).

### Ảnh hưởng Frontend
- Cập nhật `frontend/src/types/dutySchedule.ts`: `DutyType` + `DUTY_TYPE_LABELS`,
  `DutyPlanStatus` + labels, `DutySchedule` (thêm field), `DutyDayBoard`,
  `DutyWeekBoard`, `DutyWeekPlan`, `DutyWeekPlanDetail`, `DutyWeekPlanBrief`,
  `DutyWeekPlanCreate`, `DutyWeekPlanReview`.
- Cập nhật `frontend/src/api/dutySchedules.ts`: bỏ `create`; đổi `update`/`remove`
  thành thao tác dòng; thêm `dayBoard`, `weekBoard`; thêm `dutyWeekPlansApi`
  (list/get/create/update/remove/addEntry/submit/review/reopen).
- Màn hình mới `frontend/src/pages/DutyRosterPage.tsx` route `/lich-truc` (3 tab:
  Kíp trực theo ngày · Trực tuần · Bảng trực đơn vị). Gỡ khối "Lịch trực kíp" khỏi
  `AnnouncementsPage.tsx`; thêm mục NAV; thêm `Route` trong `App.tsx`.

### Migration
- DB cũ đã có bảng `duty_schedules`: chạy một lần
  `venv/Scripts/python.exe scripts/migrate_duty_schedule_unit.py` (idempotent) —
  thêm `week_plan_id`(+FK), `unit_id`(+FK), `duty_type` (default `khac`),
  `contact_phone`, `personnel_present`, `personnel_total`. Bảng `duty_week_plans`
  do `Base.metadata.create_all` tự tạo. Bản ghi cũ → `week_plan_id`/`unit_id` NULL.

### Kiểm thử đã thực hiện
- `app.openapi()` import sạch; `create_all` tạo `duty_week_plans` sạch; 82 path /
  125 operation; version 4.0.0.
- Migration MySQL: thêm đủ cột + 2 FK; chạy lại → "đã đầy đủ" (idempotent).
- Logic (gọi thẳng service): tạo bảng (Thứ Tư → chuẩn hoá Thứ Hai, "Tuần 36/2026");
  trùng (đơn vị,tuần) → 409; submit rỗng → 409; thêm dòng ngoài tuần → 400; thêm
  dòng → `unit_id`/`week_plan_id` gán từ bảng cha; submit → `cho_duyet`, cộng quân
  số 13/15; sửa dòng khi `cho_duyet` → 409; review → `da_duyet`; day board gom theo
  đơn vị + nhãn "Đã duyệt" + quân số 10/12; week board → `unit_plans`; reopen
  `da_duyet` (chỉ huy) → `nhap`; cascade xoá dòng.
- Visibility: officer đơn vị khác xem bảng `nhap` → 404, day board 0 nhóm; sau khi
  `da_duyet` → thấy, nhưng `reopen` → 403. Officer chưa gán đơn vị tạo bảng → 400.
- Runtime API (`uvicorn` cổng tạm): không JWT → 401; list/create/addEntry/submit/
  review/reopen/delete → 200/201/204 đúng; review trước submit → 409;
  `board/day` & `board/week` → 200 đúng hình dạng.

## v3.1.0 — 2026-09-02

**Người bàn giao:** Backend
**Phạm vi:** Upload file dùng chung (không gắn module nghiệp vụ cụ thể).
**Quy mô:** 74 path / 115 operation (từ 73/114 — **thêm 1 endpoint mới, không phá vỡ
client cũ** → MINOR).

### Lý do
Phục vụ mạng nội bộ LAN/offline: cần một điểm upload chung để chèn ảnh minh hoạ /
đính kèm tài liệu ở những chỗ chưa có endpoint upload riêng (vd trình soạn thảo nội
dung). Hạ tầng đã có sẵn (`app.mount("/static")`, `app/core/uploads.py`,
`MAX_UPLOAD_MB`); mục này chỉ bọc thêm một route mỏng quanh `save_upload`.

### Thêm endpoint
- `POST /api/upload` — multipart `file` (một file). Quyền: `require_roles("officer",
  "commander")` (admin kế thừa). Cho phép định dạng ảnh (`.jpg .jpeg .png .webp .gif`)
  + tài liệu (`.pdf .doc .docx .xls .xlsx .ppt .pptx`); vượt `MAX_UPLOAD_MB` (mặc định
  25) hoặc sai định dạng hoặc file rỗng → **400**; thiếu JWT → **401**; role không đủ
  → **403**. Thành công → **201** kèm `UploadOut`. File đổi tên `<uuid>.<ext>`, lưu
  `storage/uploads/common/`, phục vụ qua `/static/common/<uuid>.<ext>`.

### Thêm schema
- `UploadOut`: `{ status: "success" (const), filename: str, url: str }`.
- `Body_upload_file_api_upload_post`: `{ file: binary }` (sinh tự động).

### Ảnh hưởng Frontend
- Thêm `frontend/src/types/upload.ts` (`UploadOut`).
- Thêm `frontend/src/api/uploads.ts` (`uploadFile(file): Promise<UploadOut>`, gắn
  `Authorization: Bearer`).
- Chưa gắn UI cụ thể — dùng khi cần chèn ảnh/đính kèm ở màn hình không có endpoint
  upload riêng.

### Kiểm thử đã thực hiện
- `python -c "from app.main import app"` import sạch; `app.openapi()` → 74 path.
- Chạy uvicorn + curl: no-JWT → 401; `.txt` → 400 (kèm danh sách định dạng hợp lệ);
  ảnh PNG tên tiếng Việt có dấu + dấu cách → 201, đổi tên UUID, trả `{status, filename,
  url}`; `GET /static/common/<uuid>.png` → 200.

---

## v3.0.0 — 2026-09-01

**Người bàn giao:** Backend
**Phạm vi:** Bỏ vai trò `soldier` — chỉ cán bộ/QNCN có biên chế mới được cấp tài khoản;
bắt buộc Cấp bậc + Chức danh + Đơn vị khi tạo/kích hoạt tài khoản.
**Quy mô:** 73 path / 114 operation (từ 72/113 — **đổi enum vai trò + thêm field bắt
buộc trên `UserCreate`** → **BREAKING** → MAJOR).

### Lý do
Chỉ cán bộ và quân nhân chuyên nghiệp (QNCN) được biên chế mới có tài khoản máy
tính để đăng nhập mạng nội bộ — chiến sĩ nghĩa vụ không có tài khoản. Vai trò
`soldier` (mặc định cũ khi tự đăng ký) không còn phản ánh đúng đối tượng sử dụng
hệ thống nên bị loại bỏ.

### Đổi (BREAKING)
- `Role` (enum vai trò): `soldier | officer | commander | admin` → **`officer | commander |
  admin`**. Mọi endpoint nhận/trả `role` (`RoleUpdate`, `UserCreate.role`, `UserOut.role`)
  không còn chấp nhận `"soldier"` → **422** nếu gửi lên.
- `POST /users/register` — đổi role mặc định khi tự đăng ký từ `soldier` sang
  **`officer`** (vẫn `is_active=False`, chờ chỉ huy duyệt). Hình dạng `RegisterRequest`
  không đổi (vẫn chỉ `username`, `password`, `full_name`).
- `POST /users/` (`UserCreate`) — **thêm 2 trường bắt buộc mới**: `rank` (Cấp bậc quân
  hàm, chuỗi tự do, 1..100 ký tự) và `position` (Chức danh công tác, 1..150 ký tự).
  `unit_id` đổi từ **tuỳ chọn → bắt buộc**. Thiếu 1 trong 3 → **422**.
- `POST /users/{id}/activate` — **thêm điều kiện mới**: chỉ kích hoạt được khi tài
  khoản đã có đủ `rank`, `position` **và** `unit_id` (khác `null`/rỗng); thiếu bất kỳ
  trường nào → **409** kèm thông báo hướng dẫn bổ sung qua `/info` và `/unit`. Áp dụng
  chủ yếu cho tài khoản tự đăng ký (đăng ký nhẹ, chưa có 3 trường này).
- `UserOut` — thêm field `rank: string | null`, `position: string | null`.

### Thêm endpoint
- `PATCH /users/{id}/info` — body `{ rank, position }` (cả hai bắt buộc), chỉ
  `commander`/`admin`. Dùng để chỉ huy bổ sung/sửa Cấp bậc + Chức danh cho tài khoản
  tự đăng ký trước khi kích hoạt (kết hợp `PATCH /users/{id}/unit` đã có sẵn).

### Migration DB
- `venv/Scripts/python.exe scripts/migrate_rank_position.py` (idempotent, **bắt buộc**
  chạy trước khi dùng phiên bản này): thêm cột `users.military_rank` (ánh xạ tới field
  `rank` — đặt tên khác `rank` vì đó là từ khoá dặt trong MySQL 8, hàm cửa sổ `RANK()`),
  `users.position`; `UPDATE users SET role='officer' WHERE role='soldier'` (chuyển toàn
  bộ tài khoản `soldier` hiện có sang `officer` — các tài khoản này sẽ thiếu
  rank/position/unit nên **không kích hoạt lại được** cho tới khi chỉ huy bổ sung).

### Ảnh hưởng Frontend
- `frontend/src/types/user.ts`: `User`/`UserOut` thêm `rank`, `position`; `UserCreate`
  thêm `rank`, `position` bắt buộc, `unit_id` hết tuỳ chọn; bỏ `'soldier'` khỏi mọi
  union/label vai trò.
- `frontend/src/api/users.ts`: thêm `setInfo(id, { rank, position })` gọi
  `PATCH /users/{id}/info`.
- Màn hình: `UsersPage.tsx` (bảng "chờ duyệt" thêm ô nhập Cấp bậc/Chức danh/Đơn vị +
  nút kích hoạt gộp; bỏ "Chiến sĩ" khỏi danh sách vai trò); `ProfilePage.tsx`,
  `PortalLayout.tsx`, `DirectivesPage.tsx` (bỏ nhãn "Chiến sĩ"); `RegisterPage.tsx`
  (ghi chú chỉ huy sẽ bổ sung cấp bậc/chức danh/đơn vị khi duyệt).

### Kiểm thử đã thực hiện
- `python -c "from app.main import app"` — import sạch; `app.openapi()` build 73 path /
  114 operation.
- Migration chạy 2 lần: lần 1 thêm 2 cột + chuyển 1 tài khoản `soldier` (`lequynh`) →
  `officer`; lần 2 idempotent (0 cột thêm, 0 tài khoản chuyển).
- ORM đọc/ghi `User.rank` (cột thực `military_rank`) round-trip đúng — xác nhận việc
  đổi tên cột tránh được lỗi cú pháp `ALTER TABLE ... ADD COLUMN rank ...` (từ khoá dặt).
- Runtime (`uvicorn` + `curl`, dữ liệu test đã xoá sau khi chạy): đăng ký nhẹ → 201
  (`role=officer`, `rank/position=null`); kích hoạt ngay khi thiếu info → **409** đúng
  thông báo; `PATCH .../info` → 200; `PATCH .../unit` → 200; kích hoạt lại → 200
  (`is_active=true`); đăng nhập tài khoản vừa kích hoạt → 200 (JWT có `role=officer`).
  `POST /users/` thiếu rank/position/unit_id → 422 (đủ 3 lỗi field); đủ thông tin → 201,
  `is_active=true`, `must_change_password=true`. Gửi `role=soldier` ở cả `POST /users/`
  và `PATCH /users/{id}/role` → 422 ở cả hai.
- `scripts/export_openapi.py` → `Da xuat phien ban 3.0.0: 73 path / 114 operation`.

---

## v2.2.0 — 2026-09-01

**Người bàn giao:** Backend
**Phạm vi:** Danh bạ điện thoại (`contacts`) — nhập file danh bạ (.xlsx/.csv) & tra cứu.
**Quy mô:** 72 path / 113 operation (từ 69/108 — thêm endpoint, không xoá/đổi field cũ → MINOR).

### Thêm endpoint (`api/routes/contacts.py`, prefix `/contact-books`, yêu cầu JWT)
- `GET /contact-books` — danh sách các **bộ danh bạ** đã nhập (mỗi lần nhập file = 1 bộ tách
  riêng, không gộp). Mọi tài khoản đã đăng nhập. Trả `ContactBookOut[]` kèm `column_headers`
  (thứ tự cột gốc), `row_count`.
- `POST /contact-books` (201) — **chỉ `commander`/`admin`** (`require_roles("commander")`).
  **multipart**: `name?` (mặc định = tên file), `description?`, `file` (.xlsx hoặc .csv).
  Đọc dòng tiêu đề + mọi dòng dữ liệu; giữ **nguyên vẹn mọi cột** của file vào `Contact.extra`,
  đồng thời đoán một số trường chuẩn (`full_name`, `unit`, `position`, `phone`, `email`) theo
  tên cột tiếng Việt để tra cứu nhanh. 400 nếu: định dạng không phải .xlsx/.csv, file rỗng,
  không có dòng tiêu đề, không có dòng dữ liệu, vượt 20.000 dòng, hoặc vượt `MAX_UPLOAD_MB`.
- `GET /contact-books/{book_id}` — chi tiết 1 bộ danh bạ. 404 nếu không tồn tại.
- `DELETE /contact-books/{book_id}` (204) — xoá cả bộ (cascade toàn bộ dòng danh bạ).
  Chỉ `commander`/`admin`.
- `GET /contact-books/{book_id}/contacts` — danh sách dòng danh bạ của bộ, **phân trang**
  (`skip` `ge=0`, `limit` `1..500`, mặc định 50) + **tra cứu** `q` (LIKE trên mọi trường,
  không phân biệt hoa thường). Trả `ContactPage` = `{ items: ContactOut[], total, skip, limit,
  columns: string[] }` (`columns` = thứ tự cột gốc để FE dựng bảng động).

### Schema mới (`schemas/contact.py`)
- `ContactBookOut` (`id`, `name`, `description`, `source_file_name`, `column_headers: string[]`,
  `row_count`, `created_by_id`, `created_by_full_name`, `created_at`).
- `ContactOut` (`id`, `book_id`, `row_index`, `full_name?`, `unit?`, `position?`, `phone?`,
  `email?`, `extra: {[header: string]: string}` — **toàn bộ trường của file gốc**).
- `ContactPage` (`items`, `total`, `skip`, `limit`, `columns: string[]`).

### DB
- 2 bảng mới qua `create_all` (không cần migration): `contact_books`, `contacts`
  (FK `contact_books.id`, index `book_id`, cột `search_blob` TEXT phục vụ LIKE).
- Cột JSON dùng `app/core/types.py::JSONText` (JSON lưu dưới dạng TEXT utf8mb4) — tránh quirk
  cột MySQL `JSON` + PyMySQL làm hỏng ký tự tiếng Việt.

### Phụ thuộc mới
- `openpyxl==3.1.5` (+ `et-xmlfile==2.0.0`) — đọc .xlsx. Đã thêm vào `requirements.txt`;
  môi trường triển khai cần `pip install -r requirements.txt` lại.

### Ảnh hưởng Frontend
- Thêm `frontend/src/types/contact.ts`, `frontend/src/api/contacts.ts`.
- Trang mới `DanhBaPage` (route `/danh-ba`, nằm trong nhóm nav "Bản tin"): danh sách bộ danh bạ
  + nút "Nhập danh bạ" (chỉ commander/admin) + bảng dòng danh bạ **cột động theo file** + ô tra
  cứu + phân trang + xem chi tiết đầy đủ mọi trường của 1 người.

### Kiểm thử đã thực hiện
- `python -c "from app.main import app"` — import sạch; `app.openapi()` build 72 path /
  113 operation; `create_all` tạo đúng 2 bảng mới (`sqlalchemy.inspect`).
- Runtime (`uvicorn` + `curl`, dữ liệu test đã xoá sau khi chạy): nhập .xlsx (tiêu đề tiếng
  Việt, 3 dòng) → 201, `row_count=3`; nhập .csv → 201; đọc lại trực tiếp từ DB
  (`PYTHONIOENCODING=utf-8`) xác nhận `column_headers` và `extra` **round-trip tiếng Việt
  nguyên vẹn** (sau khi chuyển cột JSON → `JSONText`); map trường chuẩn đúng (ưu tiên cột
  "di động" cho `phone`); tra cứu `q` theo tên tiếng Việt và theo số điện thoại đều đúng;
  phân trang `skip/limit` đúng; file `.txt` → 400; bộ không tồn tại → 404; không JWT → 401;
  `DELETE` → 204 (xoá kèm dòng danh bạ). RBAC ghi/xoá dùng `require_roles("commander")` như
  các module khác.
- `scripts/export_openapi.py` → `Da xuat phien ban 2.2.0: 72 path / 113 operation`.

---

## v2.1.0 — 2026-09-01

**Người bàn giao:** Backend
**Phạm vi:** Kênh chuyên Ban Chỉ huy & Cấp uỷ (`command-threads`) — gán thành phần vào luồng,
kho văn bản chung/riêng, biên bản thảo luận tự ghép.
**Quy mô:** 69 path / 108 operation (từ 62/100 — thêm endpoint, không xoá/đổi field cũ → MINOR).

### Đổi hành vi (không đổi hình dạng response cũ, chỉ thêm field)
- **Phạm vi xem luồng đổi từ "mọi người có quyền MẬT thấy mọi luồng" sang "chỉ thành phần
  được gán mới thấy/nhắn được"**: `commander`/`admin` vẫn thấy tất cả (`command_thread_scope`
  = `"all"`); tài khoản khác chỉ thấy luồng mà mình có trong `command_thread_members`
  (scope = `"member"`). Ngoài phạm vi → **404** ở `GET /command-threads/{id}` và mọi thao tác
  trên luồng đó (không lộ tồn tại).
- `POST /command-threads` — thêm field **tuỳ chọn** `member_user_ids: int[]` (mặc định `[]`).
  Người tạo luôn tự động được thêm làm thành viên (kể cả không tự chọn mình). 404 nếu id
  không tồn tại/đã khoá.
- `CommandThreadOut` — thêm field `member_count: int`.
- `CommandThreadDetailOut` — thêm field `members: MemberOut[]` (`user_id`, `full_name`,
  `unit_name`, `added_at`).

### Thêm endpoint — Thành phần (`command_thread_members`)
- `POST /command-threads/{id}/members` (201) — `{ user_ids: int[] }`, trả về
  `CommandThreadDetailOut`. Chỉ **người tạo luồng hoặc `commander`/`admin`**; 404 nếu id không
  hợp lệ.
- `DELETE /command-threads/{id}/members/{user_id}` (204) — gỡ thành viên. Cùng quyền như trên;
  400 nếu gỡ đúng người tạo luồng; 404 nếu tài khoản không thuộc thành phần.

### Thêm endpoint — Kho văn bản (`command_thread_documents`, chung/riêng)
- `GET /command-threads/{id}/documents` — danh sách văn bản đã chia sẻ trong luồng. Văn bản
  `visibility="rieng"` chỉ hiện với người tải lên hoặc `commander`/`admin` (lọc ở service,
  không lộ trong danh sách với người khác).
- `POST /command-threads/{id}/documents` (201) — **multipart**: `title`, `visibility`
  (`chung`|`rieng`, mặc định `chung`), `file` (ảnh hoặc .pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx).
  Bất kỳ thành viên nào của luồng đều tải lên được (không riêng `commander`).
- `GET /command-threads/{id}/documents/{doc_id}/download` — `FileResponse` có kiểm soát quyền
  theo `visibility` (không qua `/static`, cùng mẫu với `official-dispatches`/`command-meetings`).
- `DELETE /command-threads/{id}/documents/{doc_id}` (204) — chỉ người tải lên hoặc
  `commander`/`admin`; xoá kèm tệp vật lý.

### Thêm endpoint — Biên bản thảo luận (`command_thread_minutes`, tự ghép — không AI)
- `POST /command-threads/{id}/minutes/generate` (201) — bất kỳ thành viên nào bấm để **tự động
  ghép** toàn bộ lịch sử luồng thành 1 bản biên bản có cấu trúc: tiêu đề luồng, thành phần tham
  gia, từng tin nhắn theo thứ tự thời gian (đánh số "Bước N", kèm tên tệp đính kèm nếu có), danh
  sách văn bản `chung` đã chia sẻ (văn bản `rieng` **không** đưa vào biên bản, chỉ ghi chú số
  lượng), trạng thái luồng tại thời điểm lập. Lưu thành 1 bản ghi mới (giữ lịch sử các lần tạo).
  Không gọi dịch vụ AI ngoài.
- `GET /command-threads/{id}/minutes` — danh sách các lần đã tạo biên bản, mới nhất trước.

### Schema mới
- `MemberAddRequest`, `MemberOut`, `CommandThreadDocumentOut`, `CommandThreadMinutesOut`,
  `DocVisibility` (`"chung" | "rieng"`).

### DB
- 3 bảng mới qua `create_all` (không cần migration): `command_thread_members`
  (unique `thread_id+user_id`), `command_thread_documents`, `command_thread_minutes`.
- Helper mới `app/core/access.py`: `command_thread_scope(user)` → `"all" | "member" | None`.

### Ảnh hưởng Frontend
- `frontend/src/types/commandDispatch.ts` (nơi định nghĩa type cho `command-threads`): thêm
  `member_count`, `members: MemberOut[]`, `CommandThreadDocument`, `CommandThreadMinutes`, và
  field `member_user_ids?` trên payload tạo luồng.
- `frontend/src/api/commandDispatches.ts` (`commandThreadsApi`): thêm `addMembers`,
  `removeMember`, `listDocuments`, `uploadDocument`, `downloadDocument`, `removeDocument`,
  `generateMinutes`, `listMinutes`; `create()` nhận thêm `memberUserIds`.
- Màn hình `KenhChiHuyPage.tsx` (tab "Họp bàn BCH & Cấp uỷ"): thêm UI chọn thành phần khi tạo
  luồng, khối "Kho văn bản" (upload chung/riêng + tải về + xoá), nút "Tạo biên bản" + xem lịch
  sử biên bản.

### Kiểm thử đã thực hiện
- `python -c "from app.main import app"` — import sạch; `app.openapi()` build được
  69 path / 108 operation; `Base.metadata.create_all` tạo đúng 3 bảng mới (xác nhận qua
  `sqlalchemy.inspect`).
- Logic (gọi thẳng service, 25 assertion, dữ liệu test tự dọn sau khi chạy): tạo luồng tự thêm
  người tạo vào thành phần; thành viên được gán xem được, ngoài thành phần → 403 (thiếu MẬT) /
  404 (có MẬT nhưng không được gán); `list_threads` lọc đúng theo scope `all`/`member`;
  add/remove members chỉ người tạo luồng hoặc BCH mới làm được, không gỡ được người tạo; kho văn
  bản: thành viên khác (không phải BCH/người tải) không thấy văn bản `rieng`; xoá văn bản chỉ
  người tải hoặc BCH; biên bản ghép đúng số tin nhắn, chứa nội dung trao đổi, **không** lộ tên
  văn bản `rieng`; người bị gỡ khỏi thành phần không tạo biên bản được nữa (404).
- Runtime (`uvicorn` + `curl`, dọn dữ liệu sau khi test): tạo luồng → 201; xem chi tiết → 200
  (đủ `members`); gửi tin → 201; tạo biên bản → 201 (nội dung đúng định dạng); danh sách biên
  bản → 200; tải lên kho văn bản → 201; danh sách kho văn bản → 200; tải file về → 200; xoá văn
  bản → 204; đóng luồng → 200; không có JWT → 401.
- `scripts/export_openapi.py` → `Da xuat phien ban 2.1.0: 69 path / 108 operation`.

---

## v2.0.0 — 2026-09-01

**Người bàn giao:** Backend
**Phạm vi:** Quản lý người dùng (`users`) — phân trang `GET /users/`.
**Quy mô:** 62 path / 100 operation (không thêm/xoá endpoint; **đổi kiểu response** của 1 endpoint → MAJOR).

### Sửa endpoint
- `GET /users/` — **BREAKING**: response đổi từ mảng `UserOut[]` sang object phân trang
  `UserPage` = `{ items: UserOut[], total: int, skip: int, limit: int }`.
  - `total` = tổng số user khớp bộ lọc `active` (không phụ thuộc `skip`/`limit`) — dùng để tính số trang.
  - Query param không đổi tên: `skip` (mặc định 0, `ge=0`), `limit` (mặc định 100, `1..500`),
    `active` (tuỳ chọn). `skip`/`limit` sai miền → **422**.
  - Quyền không đổi: chỉ `commander`/`admin`.

### Thay đổi schema
- Thêm `UserPage`: `items: UserOut[]`, `total: int`, `skip: int`, `limit: int`.
- `UserOut` không đổi.

### Ảnh hưởng Frontend
- `frontend/src/types/user.ts`: thêm `UserPage` (hoặc `Paginated<User>`).
- `frontend/src/api/users.ts`: `usersApi.list()` trả `UserPage` thay vì `User[]`.
- Màn hình bị ảnh hưởng: `UsersPage.tsx` (đọc `.items`, có thể hiển thị tổng/số trang),
  `GiaoBanTrucTuyenPage.tsx` (đọc `.items`).

### Kiểm thử đã thực hiện
- Import `app.main` OK, `API_VERSION=2.0.0`, `UserPage` validate OK.
- Service `list_users` trả `{items,total,skip,limit}` — test trực tiếp trên DB.
- Runtime (uvicorn + curl): `skip=0&limit=1` → 1 item/`total=2`; `skip=1&limit=1` → trang kế;
  `limit=0` & `skip=-1` → 422; không JWT → 401; `active=false` → `items=[]`,`total=0`.
- `scripts/export_openapi.py` → `2.0.0: 62 path / 100 operation`.

---

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
