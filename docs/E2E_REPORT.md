# Báo cáo kiểm thử chức năng toàn hệ thống (E2E)

- Sinh tự động bởi `backend/scripts/e2e_full_walkthrough.py`
- Tổng: **41** bước — **41 PASS**, **0 FAIL**
- Ảnh minh hoạ: `docs/screenshots_khai_thac/`

| # | Nhóm | Bước kiểm thử | Kết quả |
|---|------|---------------|---------|
| 1 | Khach | mo / (trang cong khai) | ✅ PASS |
| 2 | Admin | dang nhap | ✅ PASS |
| 3 | Admin | mo /bang-tin | ✅ PASS |
| 4 | Admin | mo /tin-tuc | ✅ PASS |
| 5 | Admin | mo /tin-tuc/moi | ✅ PASS |
| 6 | Admin | mo /thong-bao | ✅ PASS |
| 7 | Admin | mo /lich-truc | ✅ PASS |
| 8 | Admin | mo /danh-ba | ✅ PASS |
| 9 | Admin | mo /van-ban | ✅ PASS |
| 10 | Admin | mo /van-ban/moi | ✅ PASS |
| 11 | Admin | mo /giao-duc-chinh-tri | ✅ PASS |
| 12 | Admin | mo /giao-duc-chinh-tri/moi | ✅ PASS |
| 13 | Admin | mo /chi-thi-nhiem-vu | ✅ PASS |
| 14 | Admin | mo /chi-thi-nhiem-vu/moi | ✅ PASS |
| 15 | Admin | mo /chi-dao-bao-cao | ✅ PASS |
| 16 | Admin | mo /giao-nhiem-vu | ✅ PASS |
| 17 | Admin | mo /kenh-chi-huy | ✅ PASS |
| 18 | Admin | mo /kenh-chi-huy/cong-van/moi | ✅ PASS |
| 19 | Admin | mo /ho-so | ✅ PASS |
| 20 | Admin | mo /huong-dan | ✅ PASS |
| 21 | Admin | mo /quan-ly-nguoi-dung | ✅ PASS |
| 22 | Admin | mo /quan-ly-don-vi | ✅ PASS |
| 23 | Admin | mo luong chi dao-bao cao | ✅ PASS |
| 24 | Admin | kenh chi huy: 2 tab | ✅ PASS |
| 25 | Can bo | buoc doi mat khau lan dau | ✅ PASS |
| 26 | Can bo | doi mat khau -> vao he thong | ✅ PASS |
| 27 | Can bo | mo /tin-tuc | ✅ PASS |
| 28 | Can bo | mo /tin-tuc/moi | ✅ PASS |
| 29 | Can bo | mo /giao-duc-chinh-tri/moi | ✅ PASS |
| 30 | Can bo | mo /chi-thi-nhiem-vu | ✅ PASS |
| 31 | Can bo | mo /kenh-chi-huy | ✅ PASS |
| 32 | Can bo | mo /quan-ly-nguoi-dung | ✅ PASS |
| 33 | Can bo | nop bao cao nhiem vu | ✅ PASS |
| 34 | Nguoi dung | buoc doi mat khau lan dau | ✅ PASS |
| 35 | Nguoi dung | doi mat khau -> vao he thong | ✅ PASS |
| 36 | Nguoi dung | mo /tin-tuc | ✅ PASS |
| 37 | Nguoi dung | mo /tin-tuc/moi | ✅ PASS |
| 38 | Nguoi dung | mo /chi-thi-nhiem-vu | ✅ PASS |
| 39 | Nguoi dung | mo /kenh-chi-huy | ✅ PASS |
| 40 | Duyet | mo bai cho duyet | ✅ PASS |
| 41 | Duyet | duyet bao cao nhiem vu | ✅ PASS |

## Lỗi phát hiện trong đợt kiểm thử & đã sửa

| # | Mức | Vị trí | Mô tả | Cách sửa |
|---|-----|--------|-------|----------|
| 1 | Chặn | `frontend/src/components/PortalLayout.tsx` | `pnpm build` (`tsc -b`) hỏng: khai báo `username`, `hasClearance` không dùng. | Bỏ 2 biến khỏi `useAuth()` destructure. |
| 2 | Nặng | `frontend/src/App.css` (`button {}`, `.tab-bar .tab`, `.thread-item`) | Rule chung `button { color:#fff }` tràn vào tab và dòng danh sách (nền sáng) → chữ trắng trên nền trắng: **mất tiêu đề tab + tiêu đề luồng** ở `/kenh-chi-huy` và `/chi-dao-bao-cao`. | Thêm `color` tường minh cho `.tab-bar .tab` (+`.active`) và `.thread-item`. |
| 3 | Trung bình | `frontend/src/App.css` (`.news-thumb`) | Class `.news-thumb` trùng tên giữa thẻ tin (PostsPage) và dải ảnh nhỏ trang công khai → thumbnail PostsPage bị ép còn ~25% bề rộng, méo bố cục. | Scope lại thành `.news-article .news-thumb` / `.news-article .news-thumb-ph`. |
| 4 | Trung bình | `frontend/src/components/NewsBlock.tsx` + `App.css` | Khối "Giáo dục chính trị" ở Bảng tin và tin tiêu điểm không có ảnh bìa render khung ảnh rỗng cao ~560px (chỉ có biểu trưng) → trang trông như lỗi. | `NewsBlock` chuyển sang danh sách gọn khi không tin nào có ảnh; `FeaturedCard` bỏ hẳn khung ảnh khi thiếu ảnh; bài lead khi mở đọc chuyển từ 2 cột về 1 cột. |

## Khuyến nghị chưa xử lý (không phải lỗi chặn)

- **Nhãn vai trò**: role 4 hiển thị "Cá nhân" (cả `backend/app/core/roles.py` và `frontend/src/types/user.ts`), lệch với mô tả trong `.claude/CLAUDE.md` ("Cán bộ, sĩ quan/QNCN…"). Cần chốt thuật ngữ rồi sửa đồng bộ 2 nơi.
- **`/kenh-chi-huy` với tài khoản không đủ quyền MẬT**: backend chặn 403 đúng, nhưng frontend vẫn hiển thị form "Tạo luồng" + ô nhập. Nên ẩn toàn bộ panel, chỉ để lại thông báo không có quyền.
- **`/danh-ba`**: hiện 2 thông báo "trống" chồng nhau (panel trái + panel phải).
- **`/lich-truc`**: nút "Phê duyệt lịch trực" / "Trả lại" hiện cả khi "Chưa có bảng trực"; nút "Tải file gốc Tham mưu" gắn nhãn "Sắp có".
- Header chỉ hiển thị nhãn vai trò, **không hiển thị tên tài khoản** đăng nhập (thay đổi có chủ đích của bản đang phát triển — cân nhắc khôi phục tên cho dễ nhận biết).

