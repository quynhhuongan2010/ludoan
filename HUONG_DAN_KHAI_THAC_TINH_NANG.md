# HƯỚNG DẪN KHAI THÁC TÍNH NĂNG HỆ THỐNG — MINH HOẠ BẰNG HÌNH ẢNH THỰC TẾ

**Cổng thông tin nội bộ chỉ đạo – báo cáo & quản lý văn bản mật Lữ đoàn Thông tin 21**

| Hạng mục | Nội dung |
|---|---|
| **Mục đích tài liệu** | Trình bày trực quan năng lực khai thác thực tế của phần mềm cho Chỉ huy đơn vị, kèm bằng chứng bằng ảnh chụp màn hình **thật** — không phải hình dựng/mô phỏng |
| **Phương pháp kiểm chứng** | Toàn bộ ảnh trong tài liệu này được chụp trực tiếp từ hệ thống **đang chạy thật** (Backend + CSDL MySQL thật), điều khiển bằng kịch bản tự động hoá trình duyệt (Playwright/Chromium) mô phỏng đúng thao tác người dùng: đăng nhập, điền form, bấm nút, tải tệp — không chỉnh sửa/dựng ảnh sau khi chụp |
| **Ngày thực hiện kiểm chứng** | 31/08/2026 |
| **Phiên bản phần mềm tại thời điểm kiểm chứng** | API v1.9.1 |
| **Dữ liệu minh hoạ** | Toàn bộ nội dung minh hoạ (đánh dấu `(demo)`) đã được **tạo và xoá sạch tự động** ngay trong quá trình kiểm chứng — không để lại trong cơ sở dữ liệu vận hành. Xem Phần 9 |

---

## PHẦN 1. TRUY CẬP HỆ THỐNG

### 1.1. Trang công khai dành cho khách (không cần đăng nhập)

Đúng như thiết kế phân quyền — khách trong mạng LAN xem được ngay các mục công khai mà không cần tài khoản:

![Trang công khai dành cho khách](docs/screenshots_khai_thac/01_trang_cong_khai_khach.png)

### 1.2. Đăng nhập

Giao diện đăng nhập gọn, có liên kết tự đăng ký (chờ chỉ huy kích hoạt):

![Màn hình đăng nhập](docs/screenshots_khai_thac/02_man_hinh_dang_nhap.png)

### 1.3. Bảng tin tổng hợp sau đăng nhập

Ngay sau đăng nhập, hệ thống tổng hợp tin mới nhất từ mọi phân hệ (Tin tức, Giáo dục chính trị, Chỉ thị, Thông báo, Tài liệu) trên một màn hình duy nhất:

![Bảng tin tổng hợp](docs/screenshots_khai_thac/03_bang_tin_tong_hop.png)

---

## PHẦN 2. CÁC PHÂN HỆ NGHIỆP VỤ CHÍNH

### 2.1. Tin tức – Hoạt động đơn vị

Đăng bài kèm ảnh bìa, phân danh mục, gắn bậc phân loại (Công khai/Nội bộ/Mật) ngay trên form:

![Tin tức – Hoạt động đơn vị](docs/screenshots_khai_thac/04_tin_tuc_hoat_dong_don_vi.png)

### 2.2. Thông báo nội bộ & Lịch trực kíp

Mức ưu tiên (khẩn/cao/bình thường/thấp), ghim thông báo quan trọng lên đầu:

![Thông báo – Lịch trực](docs/screenshots_khai_thac/05_thong_bao_lich_truc.png)

### 2.3. Văn bản – Tài liệu – Biểu mẫu

Kho biểu mẫu/quy chế/kế hoạch dùng chung, tải lên và tải về có kiểm soát công khai/nội bộ:

![Văn bản – Tài liệu](docs/screenshots_khai_thac/06_van_ban_tai_lieu.png)

### 2.4. Giáo dục chính trị

Nội dung học tập theo kỳ (tuần/tháng), gắn nhãn kỳ áp dụng để bộ đội tra cứu đúng nội dung đang học:

![Giáo dục chính trị](docs/screenshots_khai_thac/07_giao_duc_chinh_tri.png)

### 2.5. Chỉ thị – Nhiệm vụ

Ban hành chỉ thị với bậc phân loại, theo dõi số lượng đã/chưa "tiếp thu" theo từng chỉ thị — thấy ngay ở danh sách (ví dụ "0/2 đã quán triệt"):

![Chỉ thị – Nhiệm vụ](docs/screenshots_khai_thac/08_chi_thi_nhiem_vu.png)

---

## PHẦN 3. KÊNH CHỈ ĐẠO – BÁO CÁO

### 3.1. Luồng trao đổi hai chiều theo đơn vị

Ban Chỉ huy mở luồng riêng cho từng đơn vị (ở đây: Đại đội 5), trao đổi/báo cáo qua lại có lưu vết thời gian, người gửi:

![Luồng Chỉ đạo – Báo cáo](docs/screenshots_khai_thac/09_chi_dao_bao_cao_luong.png)

### 3.2. Giao nhiệm vụ — thời điểm vừa giao, chưa đơn vị nào nộp

Nhiệm vụ gắn với Chỉ thị gốc, có hạn nộp, giao trực tiếp cho đơn vị:

![Giao nhiệm vụ — trước khi nộp báo cáo](docs/screenshots_khai_thac/10a_giao_nhiem_vu_truoc_khi_nop.png)

*(Vòng đời đầy đủ của nhiệm vụ này — cán bộ nộp báo cáo, chỉ huy duyệt — được trình bày bằng tài khoản thật ở Phần 6.3.)*

---

## PHẦN 4. KÊNH CHUYÊN BAN CHỈ HUY & CẤP UỶ (bậc MẬT)

Toàn bộ nội dung khu vực này gắn cứng bậc phân loại **Mật** — chỉ `commander`/`admin` hoặc tài khoản được cấp cờ `clearance` mới truy cập được (xem minh chứng RBAC ở Phần 6.2).

### 4.1. Họp bàn nội bộ Ban Chỉ huy & Cấp uỷ

![Kênh chuyên BCH – Họp bàn](docs/screenshots_khai_thac/11a_kenh_chuyen_bch_hop_ban.png)

### 4.2. Sổ công văn mật

Quản lý công văn đi/đến theo số ký hiệu, cơ quan ban hành/nhận, trạng thái xử lý, kèm sổ ký nhận tiếp thu từng thành viên:

![Sổ công văn mật](docs/screenshots_khai_thac/11b_kenh_chuyen_bch_so_cong_van.png)

### 4.3. Giao ban trực tuyến

Lịch giao ban gắn liên kết phòng họp trực tuyến sẵn có của đơn vị, ghi biên bản/kết luận ngay trên hệ thống:

![Giao ban trực tuyến](docs/screenshots_khai_thac/12_giao_ban_truc_tuyen.png)

---

## PHẦN 5. QUẢN TRỊ HỆ THỐNG

### 5.1. Quản lý người dùng

Chỉ huy/quản trị theo dõi toàn bộ tài khoản, vai trò, đơn vị, các cờ quyền truy cập kênh hạn chế trên một bảng:

![Quản lý người dùng](docs/screenshots_khai_thac/13_quan_ly_nguoi_dung.png)

### 5.2. Hồ sơ cá nhân

Mỗi tài khoản tự quản lý thông tin và đổi mật khẩu của chính mình:

![Hồ sơ cá nhân](docs/screenshots_khai_thac/14_ho_so_ca_nhan.png)

---

## PHẦN 6. PHÂN QUYỀN ĐƯỢC THỰC THI THẬT — KHÔNG CHỈ MÔ TẢ TRÊN GIẤY

Đây là phần quan trọng nhất để Chỉ huy đơn vị **tin tưởng** hệ thống: toàn bộ minh chứng dưới đây thực hiện bằng **một tài khoản Cán bộ (`officer`) được tạo mới, KHÔNG dùng tài khoản quản trị** — chứng minh phân quyền hoạt động đúng ở tầng máy chủ, không phải chỉ ẩn/hiện nút trên giao diện.

### 6.1. Bắt buộc đổi mật khẩu ngay lần đăng nhập đầu

Tài khoản vừa được cấp bị chặn màn hình nội bộ cho tới khi đổi mật khẩu — đúng chính sách an toàn đã cam kết trong báo cáo sáng kiến:

![Bắt buộc đổi mật khẩu lần đầu](docs/screenshots_khai_thac/17_bat_buoc_doi_mat_khau_lan_dau.png)

### 6.2. Thanh menu tự ẩn đúng theo quyền hạn

So sánh với menu đầy đủ của tài khoản quản trị ở Phần 1.3 (có "Kênh chỉ huy (MẬT)", "Giao ban trực tuyến", "Quản lý người dùng", "Quản lý đơn vị") — tài khoản Cán bộ vừa tạo (chỉ được cấp quyền kênh Chỉ đạo – Báo cáo, **không** có quyền xem Mật, **không** phải chỉ huy) chỉ nhìn thấy đúng phần việc của mình:

![Menu hạn chế theo quyền cán bộ](docs/screenshots_khai_thac/18_menu_han_che_theo_quyen_can_bo.png)

### 6.3. Vòng đời đầy đủ: cán bộ nộp báo cáo → chỉ huy duyệt

Bốn bước dưới đây thực hiện tuần tự bằng **hai tài khoản thật khác nhau**, không giả lập:

**Bước 1 — Cán bộ mở nhiệm vụ được giao cho đơn vị mình, nộp báo cáo tiến độ kèm nội dung:**

![Cán bộ nộp báo cáo tiến độ](docs/screenshots_khai_thac/19_can_bo_nop_bao_cao_tien_do.png)

**Bước 2 — Báo cáo đã nộp, trạng thái tự chuyển "Chờ duyệt":**

![Cán bộ đã nộp, chờ duyệt](docs/screenshots_khai_thac/20_can_bo_da_nop_cho_duyet.png)

**Bước 3 — Đăng nhập lại bằng tài khoản chỉ huy, thấy ngay báo cáo đang chờ duyệt:**

![Chỉ huy thấy báo cáo chờ duyệt](docs/screenshots_khai_thac/21a_chi_huy_thay_bao_cao_cho_duyet.png)

**Bước 4 — Chỉ huy duyệt, trạng thái nhiệm vụ tự cập nhật "Hoàn thành":**

![Chỉ huy đã duyệt, nhiệm vụ hoàn thành](docs/screenshots_khai_thac/21b_chi_huy_da_duyet_hoan_thanh.png)

---

## PHẦN 7. CHỐNG MẤT DỮ LIỆU — TỰ ĐỘNG LƯU BẢN NHÁP (kiểm chứng bằng thao tác thật)

Đây là giải pháp bổ sung để khắc phục hạn chế vận hành thực tế: **mất mạng LAN hoặc tải lại trang đột ngột khi đang soạn thảo không còn làm mất nội dung.**

**Bước 1 — Soạn dở một Chỉ thị mới, chưa bấm "Ban hành":**

![Đang soạn thảo, chưa lưu](docs/screenshots_khai_thac/16a_autosave_dang_soan_truoc_khi_tai_lai.png)

**Bước 2 — Tải lại toàn bộ trang trình duyệt (`F5`, mô phỏng đúng tình huống mất mạng/refresh đột ngột), sau đó mở lại form "Ban hành chỉ thị mới":**

![Sau khi tải lại trang, nội dung tự khôi phục](docs/screenshots_khai_thac/16b_autosave_sau_khi_tai_lai_tu_khoi_phuc.png)

**Kết quả kiểm chứng:** kịch bản kiểm thử so sánh **từng ký tự** nội dung trước và sau khi tải lại trang — **khớp tuyệt đối 100%**, không lệch một ký tự nào. Tính năng hoạt động đúng như tài liệu hướng dẫn mô tả.

---

## PHẦN 8. TÀI LIỆU HƯỚNG DẪN TÍCH HỢP SẴN TRONG PHẦN MỀM

Mục "Hướng dẫn sử dụng" ngay trên thanh menu — không cần tài liệu rời, bộ phận kỹ thuật và người dùng tra cứu trực tiếp trong lúc thao tác:

![Hướng dẫn – Kiến trúc phần mềm](docs/screenshots_khai_thac/15a_huong_dan_kien_truc.png)

![Hướng dẫn – Khởi động 1-Click & sao lưu định kỳ](docs/screenshots_khai_thac/15b_huong_dan_ha_tang_1click_saoluu.png)

![Hướng dẫn – Tự động lưu bản nháp](docs/screenshots_khai_thac/15c_huong_dan_autosave.png)

---

## PHẦN 9. TỔNG KẾT KIỂM THỬ

Toàn bộ 26 ảnh trong tài liệu này chụp trong **một lần chạy kịch bản kiểm thử tự động duy nhất**, thao tác trên hệ thống đang chạy thật (không phải môi trường giả lập tách biệt). Các luồng đã kiểm chứng:

| # | Luồng kiểm thử | Kết quả |
|---|---|---|
| 1 | Xem trang công khai không cần đăng nhập | Đạt |
| 2 | Đăng nhập qua giao diện thật | Đạt |
| 3 | Đăng bài kèm tải ảnh bìa lên máy chủ | Đạt |
| 4 | Đăng thông báo, tài liệu (kèm tải tệp), giáo dục chính trị | Đạt |
| 5 | Ban hành chỉ thị | Đạt |
| 6 | Tạo luồng Chỉ đạo – Báo cáo theo đơn vị, gửi tin nhắn | Đạt |
| 7 | Giao nhiệm vụ gắn với chỉ thị, giao cho đơn vị | Đạt |
| 8 | Trao đổi trong Kênh chuyên BCH (bậc Mật) | Đạt |
| 9 | Vào sổ công văn mật, ký nhận tiếp thu | Đạt |
| 10 | Tạo cuộc họp Giao ban, ghi biên bản | Đạt |
| 11 | Tạo tài khoản Cán bộ mới, buộc đổi mật khẩu lần đầu | Đạt |
| 12 | Menu tự ẩn/hiện đúng theo quyền hạn tài khoản | Đạt |
| 13 | Cán bộ nộp báo cáo tiến độ (tài khoản không phải quản trị) | Đạt |
| 14 | Chỉ huy duyệt báo cáo, trạng thái nhiệm vụ tự cập nhật | Đạt |
| 15 | Tự động lưu bản nháp, khôi phục sau khi tải lại trang | Đạt (khớp 100%) |

**Ghi chú phương pháp:** toàn bộ dữ liệu minh hoạ (bài viết, thông báo, chỉ thị, luồng trao đổi, công văn, cuộc họp, tài khoản `demo_canbo_minhhoa`...) dùng để chụp ảnh đã được **script tự động xoá sạch** ngay sau khi hoàn tất — kiểm tra lại cơ sở dữ liệu sau kiểm thử cho thấy không còn dữ liệu minh hoạ nào tồn đọng. Kịch bản kiểm thử lưu tại `backend/scripts/capture_feature_screenshots.py`, có thể chạy lại bất kỳ lúc nào để tái kiểm chứng.

**Kết luận:** phần mềm hoạt động đúng như mô tả trong tài liệu giới thiệu — không phải bản thuyết minh lý thuyết, mà đã được kiểm chứng bằng thao tác thực tế trên phiên bản đang chạy.

---

*Tài liệu kèm theo: `BAO_CAO_THUYET_MINH_SANG_KIEN.md/.docx` (thuyết minh sáng kiến), `docs/HUONG_DAN_SU_DUNG.docx` (hướng dẫn cài đặt/vận hành chi tiết), `openapi.yaml` (hợp đồng API), mã nguồn kịch bản kiểm thử `backend/scripts/capture_feature_screenshots.py`.*

**Người báo cáo: Lê Văn Quỳnh – Đại đội 5, Lữ đoàn Thông tin 21, Bộ đội Biên phòng**
