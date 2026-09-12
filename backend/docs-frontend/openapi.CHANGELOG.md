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
