# BÁO CÁO THUYẾT MINH SÁNG KIẾN

**Tên sáng kiến:** Xây dựng Cổng thông tin nội bộ Lữ đoàn Thông tin 21 – nền tảng số hoá công tác tuyên truyền, chỉ đạo – báo cáo và quản lý văn bản mật trong mạng nội bộ đơn vị

| Hạng mục | Nội dung |
|---|---|
| **Tác giả sáng kiến** | Đồng chí Lê Văn Quỳnh |
| **Đơn vị công tác** | Đại đội 5, Lữ đoàn Thông tin 21, Bộ đội Biên phòng |
| **Thời gian nghiên cứu & phát triển** | Tháng 05/2026 – Tháng 08/2026 |
| **Phương pháp thực hiện** | Ứng dụng kỹ thuật Vibecoding kết hợp trí tuệ nhân tạo (AI-driven development): thiết kế kiến trúc 3 tầng chuẩn mực, tự động hoá quy trình Contract-First, kiểm thử toàn diện |
| **Lĩnh vực áp dụng** | Công nghệ thông tin – Cải cách hành chính quân sự – Bảo mật thông tin |
| **Phiên bản phần mềm tại thời điểm báo cáo** | API v1.9.1 |

---

## PHẦN 1. ĐẶT VẤN ĐỀ VÀ TÍNH CẤP THIẾT

### 1.1. Thực trạng công tác quản lý thông tin tại đơn vị

Lữ đoàn Thông tin 21 là đơn vị bảo đảm thông tin liên lạc cho Bộ đội Biên phòng, có địa bàn đóng quân phân tán, nhiều đầu mối (các phòng ban cơ quan Lữ đoàn, Tiểu đoàn 1, Tiểu đoàn 2, Đại đội 5, Trạm bảo đảm, Trung tâm 2…). Qua theo dõi thực tế, công tác quản lý thông tin – văn bản của đơn vị còn một số bất cập:

- **Tuyên truyền chính trị, phổ biến hoạt động đơn vị** chủ yếu qua bảng tin giấy, họp trực tiếp hoặc các nhóm nhắn tin dân sự → nội dung phân tán, khó lưu trữ, khó tra cứu lại, không kiểm soát được ai đã tiếp nhận.
- **Luồng chỉ đạo – báo cáo** giữa Ban Chỉ huy Lữ đoàn và các đơn vị cấp dưới đi qua nhiều khâu trung gian (điện thoại, văn bản giấy, giao liên) → chậm, dễ thất lạc, khó theo dõi tiến độ giao – nhận – hoàn thành nhiệm vụ.
- **Văn bản, tài liệu, biểu mẫu** dùng chung không có nơi lưu trữ tập trung; cán bộ, chiến sĩ mất thời gian tìm kiếm bản mới nhất, dễ dùng nhầm biểu mẫu cũ.
- **Giáo dục chính trị** theo tuần/tháng thiếu kênh phát hành thống nhất, khó bảo đảm 100% quân số tiếp cận đúng nội dung, đúng thời điểm.
- **Thông tin có độ mật khác nhau** (công khai, nội bộ, mật) bị xử lý chung một cách thủ công, phụ thuộc ý thức từng người → tiềm ẩn nguy cơ lộ, lọt.
- **Sử dụng các nền tảng dân sự** (mạng xã hội, ứng dụng nhắn tin, lưu trữ đám mây) để trao đổi công việc là **vi phạm quy định bảo mật**, dữ liệu nằm ngoài tầm kiểm soát của đơn vị.

### 1.2. Tính cấp thiết

- **Yêu cầu bảo mật:** Thông tin quân sự bắt buộc phải được xử lý, lưu trữ trong hệ thống do đơn vị làm chủ hoàn toàn, cách ly khỏi Internet. Cần một nền tảng chạy **offline 100%** trong mạng nội bộ (LAN/WAN quân sự).
- **Yêu cầu cải cách hành chính:** Nghị quyết, chỉ thị các cấp về đẩy mạnh chuyển đổi số, cải cách hành chính, xây dựng "đơn vị số" đòi hỏi giảm giấy tờ, tăng tốc độ xử lý công việc, minh bạch tiến độ.
- **Yêu cầu chỉ huy – điều hành:** Ban Chỉ huy cần công cụ giao nhiệm vụ, theo dõi tiến độ, nắm mức độ quán triệt chỉ thị theo thời gian thực, đến từng đơn vị, từng cá nhân.
- **Nguồn lực hạn chế:** Đơn vị không có biên chế lập trình viên chuyên trách, không có kinh phí mua phần mềm thương mại. Cần một giải pháp **tự chủ, chi phí thấp, dễ tiếp nhận và duy trì**.

### 1.3. Mục tiêu của sáng kiến

1. Xây dựng một cổng thông tin nội bộ **thống nhất, tập trung**, phục vụ đồng thời hai nhiệm vụ: tuyên truyền chính trị – hoạt động đơn vị và triển khai nhiệm vụ có kiểm soát truy cập.
2. Số hoá trọn vẹn luồng **chỉ đạo – báo cáo** và **giao – nhận – nghiệm thu nhiệm vụ** giữa Ban Chỉ huy và các đơn vị.
3. Thiết lập cơ chế **phân quyền nhiều cấp (RBAC)** và **phân loại thông tin 3 mức** (Công khai – Nội bộ – Mật) được thực thi bắt buộc ở máy chủ.
4. Bảo đảm hệ thống **hoạt động hoàn toàn trong mạng nội bộ, không phụ thuộc Internet**, đơn vị làm chủ mã nguồn và dữ liệu.
5. Bàn giao kèm tài liệu hướng dẫn để bộ phận kỹ thuật của đơn vị **tự cài đặt, vận hành, xử lý sự cố**.

---

## PHẦN 2. NỘI DUNG MÔ HÌNH SÁNG KIẾN

### 2.1. Kiến trúc tổng thể

Hệ thống là một ứng dụng web **Fullstack** chạy khép kín trong mạng nội bộ:

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| **Backend** | FastAPI (Python), Uvicorn | Xử lý nghiệp vụ, xác thực JWT, phân quyền, cung cấp API tại cổng `8000`; tự sinh tài liệu API tại `/docs` |
| **Cơ sở dữ liệu** | MySQL (`ludoan_db`) | Lưu trữ toàn bộ dữ liệu nghiệp vụ |
| **Frontend** | React + TypeScript + Vite | Giao diện người dùng, đóng gói tĩnh, chạy trên trình duyệt phổ thông (Chrome, Cốc Cốc, Edge) |
| **Lưu trữ tệp** | Ổ đĩa máy chủ (`storage/uploads/`) | Ảnh, văn bản, công văn đính kèm; phục vụ qua đường dẫn `/static` |

**Đặc điểm nổi bật:** không có bất kỳ phụ thuộc nào ra Internet; toàn bộ thư viện, phông chữ, mã giao diện và dữ liệu nằm trên máy chủ nội bộ. Cấu hình bảo mật (mật khẩu CSDL, khoá JWT, tài khoản quản trị) đọc từ tệp `.env`, **không mã hoá cứng trong mã nguồn**.

**Đóng gói vận hành sản xuất — 1 tiến trình, 1 cổng duy nhất:** bản build tĩnh của Frontend (`npm run build` → `frontend/dist`) được chính Backend FastAPI phục vụ luôn (route dự phòng SPA đăng ký sau cùng, không che bất kỳ endpoint API nào — xem `backend/app/main.py`). Nhờ vậy máy chủ nội bộ chỉ cần chạy **một tiến trình Uvicorn duy nhất trên một cổng `8000`**, thay vì hai tiến trình song song (Frontend cổng 5173 + Backend cổng 8000) như môi trường phát triển — giảm số cổng phải mở trên tường lửa, giảm số tiến trình bộ phận kỹ thuật phải giám sát, tối ưu tài nguyên (RAM, handle mạng) cho máy chủ cấu hình vừa phải đặt tại đơn vị. Frontend gọi API bằng đường dẫn tương đối (`frontend/.env.production`), tự khớp với địa chỉ đang truy cập (`localhost` hay bất kỳ IP LAN nào của máy chủ) mà không phải build lại riêng cho từng địa chỉ.

### 2.2. Kiến trúc 3 tầng chuẩn mực

Mỗi chức năng nghiệp vụ được tách bạch trách nhiệm thành 3 tầng, không viết logic hay truy vấn thẳng trong tầng route:

| Tầng | Thư mục | Trách nhiệm |
|---|---|---|
| **Route (API)** | `app/api/routes/` | Khai báo đường dẫn, phương thức, mã trạng thái, kiểm tra quyền (`Depends`) |
| **Service (nghiệp vụ)** | `app/services/` | Quy tắc nghiệp vụ, kiểm tra sở hữu, lọc theo bậc mật, sinh lỗi 403/404/409 |
| **Repository (dữ liệu)** | `app/repositories/` | Truy vấn CSDL thuần tuý: create / list / get / update / delete |

Ưu điểm: dễ kiểm thử từng tầng, dễ bảo trì, dễ mở rộng module mới theo đúng khuôn mẫu, giảm rủi ro lỗi khi bàn giao cho người khác tiếp quản.

### 2.3. Phương pháp triển khai Vibecoding kết hợp trí tuệ nhân tạo

Sáng kiến được thực hiện bằng phương pháp **Vibecoding** – phát triển phần mềm có sự tham gia dẫn dắt của trí tuệ nhân tạo (AI-driven development), trong đó tác giả giữ vai trò kiến trúc sư và người kiểm soát chất lượng:

1. **Chuẩn hoá bối cảnh nghiệp vụ thành bộ quy tắc bắt buộc** (`.claude/CLAUDE.md`): mô tả cơ cấu tổ chức, quy ước vai trò, sơ đồ chức năng, quy tắc phân quyền. Trí tuệ nhân tạo phải tuân thủ tuyệt đối các quy tắc này khi sinh mã.
2. **Đóng gói quy trình thành "kỹ năng" (skill) tái sử dụng:**
   - `fast-api-mysql-auto-schema`: tự động sinh mã 3 tầng (model → schema → repository → service → route) theo cấu trúc chuẩn.
   - `contract-first-handshake`: quy trình 5 bước bắt buộc để đồng bộ hợp đồng API giữa Backend và Frontend.
3. **Quy trình Contract-First:** sau mỗi thay đổi API, hệ thống xuất lại tệp hợp đồng `openapi.yaml`, ghi biên bản bàn giao vào `openapi.CHANGELOG.md` (đánh phiên bản khớp `API_VERSION`), rồi mới sinh kiểu dữ liệu và lớp gọi API phía Frontend → hai phía **luôn khớp nhau**, không lệch hợp đồng.
4. **Kiểm thử toàn diện:** bộ kịch bản kiểm thử tự động (`backend/scripts/test_full_system.py`, `test_post_rbac.py`…) chạy lại toàn bộ luồng đăng nhập – phân quyền – nghiệp vụ – phân loại mật sau mỗi lần thay đổi, bảo đảm không phá vỡ chức năng cũ.
5. **Sinh tài liệu tự động:** tài liệu hướng dẫn sử dụng (`docs/HUONG_DAN_SU_DUNG.docx`) và ảnh minh hoạ được sinh bằng script, luôn cập nhật theo phiên bản phần mềm.

**Giá trị của phương pháp:** một cá nhân, không có ê-kíp lập trình, vẫn hoàn thành một hệ thống nhiều phân hệ, chất lượng mã đồng đều, tài liệu đầy đủ, trong thời gian ngắn (khoảng 4 tháng), chi phí gần như bằng không.

### 2.4. Cơ chế phân quyền và bảo mật thông tin

**Phân quyền RBAC 4 cấp** (trường `role` của tài khoản):

| Vai trò | Đối tượng thực tế | Quyền chính |
|---|---|---|
| `admin` | Quản trị hệ thống (chủ đơn vị giữ) | Toàn quyền `commander` + độc quyền: cấp cờ kênh hạn chế, cấp lại mật khẩu, quản lý đơn vị, tạo `admin` khác |
| `commander` | Lữ trưởng, Chính uỷ, Phó Lữ trưởng, Phó Chính uỷ | Ban hành chỉ thị, duyệt/đăng mọi nội dung, quản lý tài khoản |
| `officer` | Cán bộ, sĩ quan/QNCN phòng ban, đại đội | Đăng/biên tập Tin tức – Hoạt động và Giáo dục chính trị |
| `soldier` | Chiến sĩ (mặc định khi tự đăng ký) | Chỉ xem nội dung được phép |

- Xác thực bằng **JWT** (token có hạn 24 giờ, cấu hình được).
- Quyền được **thực thi bắt buộc tại tầng Service của Backend**; giao diện chỉ ẩn/hiện nút cho gọn.
- Đăng ký công khai tạo tài khoản `soldier` ở trạng thái chờ; chỉ đăng nhập được sau khi chỉ huy **kích hoạt**.
- Ràng buộc an toàn: không tự hạ quyền/khoá chính mình; luôn giữ tối thiểu 1 `commander` đang hoạt động.

**Phân loại thông tin 3 mức** (áp cho tin bài, chỉ thị, tài liệu):

| Bậc | Giá trị | Phạm vi xem |
|---|---|---|
| Công khai | `cong_khai` | Mọi máy trong LAN, không cần đăng nhập |
| Nội bộ | `noi_bo` | Mọi tài khoản đã kích hoạt |
| Mật | `mat` | `commander`/`admin` HOẶC tài khoản có cờ `clearance = true` |

Việc lọc theo bậc mật thực hiện ở tầng Service: danh sách chỉ trả các mục người dùng được phép; truy cập trực tiếp một mục vượt quyền trả về 404 (không lộ sự tồn tại).

### 2.5. Các tính năng cốt lõi (5 Phase đã hoàn thành)

#### Nhóm nền tảng (đã triển khai trước Phase 1)

- **Trang chủ / Bảng tin:** tổng hợp tin mới nhất, giáo dục chính trị, chỉ thị, thông báo.
- **Tin tức – Hoạt động đơn vị:** danh mục huấn luyện, dân vận, khen thưởng, gương người tốt; luồng duyệt bài (cán bộ đăng → chờ duyệt → chỉ huy duyệt/trả lại); upload ảnh bìa.
- **Thông báo nội bộ & Lịch trực kíp:** mức ưu tiên, ghim, thời hạn hiệu lực; lịch trực theo ngày/ca.
- **Văn bản – Tài liệu – Biểu mẫu:** upload/tải về tệp Office/PDF, phân chuyên mục, kiểm soát công khai.
- **Giáo dục chính trị:** nội dung theo tuần/tháng (nhãn kỳ áp dụng), tài liệu đính kèm.
- **Chỉ thị – Nhiệm vụ:** trạng thái nháp/đã ban hành; nút "Tôi đã tiếp thu" (điểm danh quán triệt); chỉ huy xem danh sách đã/chưa tiếp thu.
- **Quản lý người dùng, Quản lý đơn vị, Hồ sơ cá nhân, Đổi mật khẩu.**

#### Phase 1 – Tài khoản quản trị hệ thống (`admin`)

Tách vai trò quản trị kỹ thuật khỏi vai trò chỉ huy. Tài khoản `admin` khởi tạo sẵn (thông tin lấy từ `.env`), có cờ chống khoá/hạ quyền, buộc đổi mật khẩu lần đầu; độc quyền quản lý đơn vị và cấp các cờ truy cập kênh hạn chế. Kèm cơ cấu đơn vị chuẩn được seed tự động.

#### Phase 2 – Kênh Chỉ đạo – Báo cáo (luồng trao đổi)

Luồng hội thoại có kiểm soát phạm vi giữa Ban Chỉ huy và từng đơn vị: tạo luồng theo đơn vị, gửi tin kèm tệp đính kèm, đánh dấu đã đọc, đóng luồng (chỉ chỉ huy). Ban Chỉ huy thấy mọi luồng; đơn vị cấp dưới chỉ thấy luồng của đơn vị mình.

#### Phase 3 – Kênh Chỉ đạo – Báo cáo (giao nhiệm vụ)

Giao nhiệm vụ đến đơn vị hoặc cá nhân, có hạn nộp; đơn vị nộp báo cáo (nội dung + tệp), chỉ huy duyệt/trả lại; trạng thái nhiệm vụ (chưa giao / đang thực hiện / hoàn thành / quá hạn) tự tính lại theo tiến độ nộp và duyệt. Lưu đầy đủ lịch sử các lần nộp.

#### Phase 4 – Kênh chuyên Ban Chỉ huy & Cấp uỷ (MẬT)

Không gian trao đổi gắn cứng bậc `mat`, chỉ dành cho người có quyền xem mật. Gồm: luồng họp bàn nội bộ; **Sổ công văn mật** (quản lý công văn đi/đến, số ký hiệu, trích yếu, trạng thái xử lý, tệp đính kèm) kèm **sổ ký nhận tiếp thu** của từng thành viên. Tệp công văn tải về qua kênh có kiểm soát quyền riêng, không đi qua `/static`.

#### Phase 5 – Giao ban trực tuyến (MẬT)

Quản lý lịch giao ban của Ban Chỉ huy & Cấp uỷ: thời gian, địa điểm, liên kết phòng họp (dùng hạ tầng họp sẵn có của đơn vị, hệ thống không tự dựng video), chương trình, biên bản/kết luận, tài liệu đính kèm. Mời – gỡ thành phần dự; điểm danh (có mặt / vắng mặt / chưa điểm danh), lý do vắng, ý kiến đóng góp — thành viên tự cập nhật phần của chính mình.

### 2.6. Khắc phục hạn chế vận hành thực tế: đóng gói 1-Click và bảo đảm an toàn dữ liệu

Qua rà soát vận hành thử tại đơn vị, sáng kiến bổ sung một nhóm giải pháp nhắm thẳng vào 3 rủi ro thực tế: **khởi động hệ thống phức tạp** đối với cán bộ không chuyên CNTT, **mất nội dung đang soạn** khi rớt mạng/mất điện, và **không có cơ chế phục hồi** khi sự cố xảy ra với máy chủ.

**a) Đóng gói 1-Click, tối ưu tài nguyên máy chủ mạng nội bộ**

- File `Chay_He_Thong.bat` ở thư mục gốc: bộ phận kỹ thuật chỉ cần **bấm đúp chuột** — tự kích hoạt môi trường ảo Python, tự kiểm tra `venv`/`.env`/bản build Frontend đã sẵn sàng chưa (báo lỗi rõ ràng thay vì treo im lặng), rồi khởi động máy chủ sản xuất (`uvicorn --host 0.0.0.0 --port 8000`, **không** bật cờ `--reload` của môi trường phát triển) — không cần thao tác dòng lệnh.
- Kết hợp với kiến trúc 1 cổng duy nhất (mục 2.1), toàn bộ hệ thống — cả giao diện lẫn API — chạy trong **đúng 1 tiến trình**, giảm một nửa số cổng cần mở tường lửa (`8000` thay vì `8000` + `5173`) và số tiến trình phải giám sát, phù hợp máy chủ cấu hình vừa phải sẵn có tại đơn vị.

**b) Chống mất dữ liệu do rớt mạng LAN / mất điện khi đang soạn thảo**

- Các form soạn thảo nội dung dài và quan trọng nhất — ban hành **Chỉ thị**, trao đổi/báo cáo trong **Kênh Chỉ đạo – Báo cáo**, tạo/nộp báo cáo tiến độ ở **Giao nhiệm vụ**, trao đổi trong **Kênh chuyên BCH & Cấp uỷ**, và **biên bản Giao ban trực tuyến** — được trang bị cơ chế **tự động lưu bản nháp** (autosave draft) ngay trên trình duyệt máy trạm trong lúc gõ, không cần thao tác lưu riêng.
- Khi máy trạm bị tải lại trang, mất điện hoặc rớt mạng LAN đột ngột trước khi kịp bấm gửi/ban hành/lưu, mở lại đúng mục đó nội dung **tự khôi phục**; sau khi gửi/lưu thành công, bản nháp tạm được xoá để không bung lại nội dung cũ ở lần soạn sau. Đây là lưới an toàn tại **máy trạm**, không thay thế cho việc bấm gửi/lưu — dữ liệu chỉ thật sự an toàn khi máy chủ đã ghi nhận.

**c) Sao lưu và phục hồi CSDL định kỳ, tự động**

- Script `backend/scripts/backup_db.py` sao lưu toàn bộ CSDL MySQL ra file **nén gzip** (`.sql.gz`) tại `backend/storage/backups/`, đọc thông tin kết nối từ `.env` (mật khẩu truyền qua biến môi trường tiến trình con, không hiện trên dòng lệnh hay Task Manager). Tự động giữ lại 14 bản gần nhất, xoá bớt bản cũ để không làm đầy ổ đĩa.
- Có thể chạy tay hoặc đặt lịch **tự động hằng ngày** qua Windows Task Scheduler (hướng dẫn chi tiết trong tài liệu bàn giao) — bảo đảm luôn có bản sao lưu gần nhất, không phụ thuộc việc "nhớ ra để sao lưu".
- Kèm lệnh phục hồi một bước (`backup_db.py --restore <file>.sql.gz`, có bước xác nhận trước khi ghi đè) để bộ phận kỹ thuật khôi phục nhanh khi máy chủ gặp sự cố (hỏng CSDL, ngắt điện đột ngột giữa lúc ghi).

---

## PHẦN 3. HIỆU QUẢ THỰC TẾ MANG LẠI

### 3.1. Về tốc độ và hiệu quả xử lý công việc

- **Rút ngắn luồng chỉ đạo – báo cáo:** chỉ thị, nhiệm vụ được ban hành và đến đơn vị **ngay lập tức**, thay cho quy trình qua nhiều khâu trung gian. Ban Chỉ huy theo dõi tiến độ giao – nhận – hoàn thành nhiệm vụ theo thời gian thực, đến từng đơn vị.
- **Nắm chắc mức độ quán triệt:** với mỗi chỉ thị, hệ thống hiển thị danh sách đã/chưa "tiếp thu" theo từng quân nhân, giúp chỉ huy đôn đốc có trọng điểm.
- **Giảm thời gian tra cứu:** văn bản, biểu mẫu, tài liệu giáo dục chính trị tập trung một nơi, luôn là bản mới nhất; cán bộ, chiến sĩ tự tra cứu không phải hỏi lại.
- **Giảm giấy tờ:** tin bài, thông báo, báo cáo tiến độ, biên bản giao ban được lưu và luân chuyển dưới dạng số.

### 3.2. Về bảo mật dữ liệu

- **Dữ liệu nằm hoàn toàn trong mạng nội bộ**, trên máy chủ do đơn vị làm chủ; không có kết nối ra Internet, loại bỏ nguy cơ rò rỉ qua nền tảng dân sự.
- **Phân loại 3 mức thông tin được máy chủ thực thi bắt buộc** — người không đủ quyền không thể xem, kể cả khi biết đường dẫn.
- **Kênh mật tách biệt** cho Ban Chỉ huy & Cấp uỷ; công văn mật có sổ ký nhận, tải về qua kênh kiểm soát riêng.
- **Không lộ thông tin nhạy cảm trong mã nguồn:** toàn bộ mật khẩu, khoá bí mật đọc từ `.env`.
- **Nhật ký thao tác quan trọng** (duyệt bài, giao nhiệm vụ, ký nhận công văn, điểm danh) được lưu vết phục vụ kiểm tra.

### 3.3. Về độ tin cậy vận hành và an toàn dữ liệu

- **Khởi động đơn giản hoá:** từ 2 tiến trình/2 cổng (môi trường phát triển) còn **1 cú bấm đúp** (`Chay_He_Thong.bat`) trên **1 cổng duy nhất** — bộ phận kỹ thuật không chuyên sâu CNTT vẫn tự vận hành được, không phụ thuộc tác giả có mặt.
- **Không mất nội dung đang soạn** khi rớt mạng LAN hoặc mất điện đột ngột tại máy trạm: cơ chế tự động lưu bản nháp khôi phục lại đúng nội dung đang gõ ở các form chỉ đạo/báo cáo quan trọng nhất.
- **Có cơ chế phục hồi khi sự cố xảy ra ở máy chủ:** sao lưu CSDL nén, tự động hằng ngày, tự dọn bản cũ; lệnh phục hồi một bước — rút ngắn thời gian khôi phục hoạt động từ "mất dữ liệu vĩnh viễn" xuống còn "chậm tối đa 1 ngày làm việc" (tính từ lần sao lưu gần nhất).

### 3.4. Về tính tự chủ và chi phí

- **Chi phí phát triển gần như bằng không:** một cá nhân thực hiện bằng phương pháp Vibecoding trong ~4 tháng, không thuê ngoài, không mua phần mềm thương mại.
- **Công nghệ nguồn mở, phổ biến** (Python/FastAPI, MySQL, React) — dễ tìm tài liệu, dễ tuyển/bồi dưỡng người duy trì.
- **Đơn vị làm chủ toàn bộ mã nguồn**, có thể tự sửa đổi, mở rộng theo yêu cầu nhiệm vụ.
- **Kiến trúc 3 tầng + quy trình Contract-First + bộ kiểm thử tự động** giúp việc bàn giao và tiếp nhận thuận lợi, giảm phụ thuộc vào tác giả.

### 3.5. Khả năng nhân rộng

Mô hình có thể áp dụng cho các đơn vị cùng cấp trong Bộ đội Biên phòng có nhu cầu và điều kiện hạ tầng mạng nội bộ tương tự. Cơ cấu đơn vị, quy ước vai trò và danh mục nội dung đều cấu hình được, không phải viết lại mã.

---

## PHẦN 4. HƯỚNG DẪN CÀI ĐẶT, VẬN HÀNH VÀ XỬ LÝ SỰ CỐ

> Phần này dành cho bộ phận kỹ thuật tiếp nhận hệ thống. Bản đầy đủ kèm ảnh minh hoạ: `docs/HUONG_DAN_SU_DUNG.docx`. Trên phần mềm: mục **Hướng dẫn sử dụng** trên thanh menu.

### 4.1. Yêu cầu hạ tầng

| Hạng mục | Yêu cầu |
|---|---|
| Máy chủ | Windows/Linux; đã cài Python 3.11+, MySQL 8.x, Node.js 18+ (chỉ cần khi build Frontend) |
| Máy chủ – địa chỉ | **IP tĩnh** trong dải LAN đơn vị (ví dụ `192.168.1.10`) |
| Máy trạm | Trình duyệt Chrome / Cốc Cốc / Edge; cùng mạng LAN, ping thông máy chủ |
| Kết nối Internet | **Không cần** — hệ thống hoạt động offline 100% |
| Cổng dịch vụ | **Vận hành sản xuất (khuyến nghị): chỉ `8000`** (Backend phục vụ luôn cả giao diện lẫn API). `5173` chỉ cần khi chạy Frontend tách rời ở chế độ phát triển |

### 4.2. Cấu hình IP tĩnh cho máy chủ

Đặt bằng dòng lệnh (PowerShell/CMD quyền Administrator), ví dụ:

```
netsh interface ip set address name="Ethernet" static 192.168.1.10 255.255.255.0 192.168.1.1
```

Hoặc: *Control Panel → Network and Sharing Center → Change adapter settings →* chuột phải card mạng *→ Properties → Internet Protocol Version 4 (TCP/IPv4) → Properties →* chọn *Use the following IP address*.

CORS của Backend đã mở sẵn cho `localhost`/`127.0.0.1` và các dải LAN riêng `10.x`, `192.168.x`, `172.16–31.x`. Nếu dùng dải khác, bổ sung origin vào `EXTRA_CORS_ORIGINS` trong `backend/.env`.

### 4.3. Thông tuyến tường lửa

**Vận hành sản xuất (khuyến nghị) — chỉ cần mở cổng `8000`:**

```
netsh advfirewall firewall add rule name="LuDoan21 He thong 8000" dir=in action=allow protocol=TCP localport=8000
```

Kiểm tra từ máy trạm: mở `http://192.168.1.10:8000` — phải thấy ngay giao diện Cổng thông tin (không phải trang JSON) vì Backend đã phục vụ luôn cả Frontend.

*(Chỉ khi chạy Frontend tách rời ở chế độ phát triển mới cần mở thêm cổng `5173`:* `netsh advfirewall firewall add rule name="LuDoan21 Web Dev 5173" dir=in action=allow protocol=TCP localport=5173`*)*

### 4.4. Cấu hình và khởi động

**Tệp `backend/.env`** (không mã hoá cứng trong mã nguồn):

| Biến | Ý nghĩa |
|---|---|
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DB`, `MYSQL_USER`, `MYSQL_PASSWORD` | Thông tin kết nối MySQL |
| `DATABASE_URL` | Chuỗi kết nối SQLAlchemy (ký tự đặc biệt trong mật khẩu phải mã hoá URL, ví dụ `@` → `%40`) |
| `JWT_SECRET_KEY`, `JWT_EXPIRE_MINUTES` | Khoá ký token và thời hạn phiên (mặc định 1440 phút = 24 giờ) |
| `MAX_UPLOAD_MB` | Giới hạn dung lượng tệp tải lên (mặc định 50) |
| `EXTRA_CORS_ORIGINS` | Bổ sung origin cho phép ngoài dải LAN mặc định |
| `SYSTEM_ADMIN_USERNAME`, `SYSTEM_ADMIN_PASSWORD` | Tài khoản quản trị khởi tạo lần đầu |

**Tệp `frontend/.env.production`:** `VITE_API_BASE_URL=` (để rỗng) — Frontend gọi API bằng đường dẫn tương đối, tự khớp mọi địa chỉ máy chủ, không cần build lại riêng cho từng IP. (`frontend/.env` — dùng khi chạy Frontend tách rời ở chế độ phát triển — vẫn khai IP tĩnh máy chủ như trước.)

**Khởi động sản xuất — 1-Click (khuyến nghị):** bấm đúp file **`Chay_He_Thong.bat`** ở thư mục gốc dự án. File tự kích hoạt `venv`, kiểm tra cấu hình, rồi khởi động máy chủ Uvicorn ở chế độ sản xuất (không bật `--reload`) trên cổng `8000` — phục vụ đồng thời cả giao diện lẫn API. Dừng bằng cách đóng cửa sổ dòng lệnh hoặc `Ctrl+C`.

**Lệnh khởi động thủ công (khi cần chạy tay/gỡ lỗi):**

```
# 1) Build Frontend (chỉ cần làm lại khi có thay đổi giao diện)
cd frontend
npm install
npm run build       # kết quả trong frontend/dist

# 2) Backend (đồng thời phục vụ Frontend tĩnh vừa build)
cd backend
venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Chế độ phát triển (2 tiến trình tách rời, chỉ dùng khi đang sửa mã):
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Lần đầu chạy Backend sẽ tự tạo bảng và seed tài khoản `admin` cùng cơ cấu đơn vị chuẩn. Khi nâng cấp từ bản cũ, chạy các script migration trong `backend/scripts/` theo đúng thứ tự ghi trong tài liệu kỹ thuật.

### 4.5. Cẩm nang xử lý sự cố thường gặp

| # | Sự cố | Triệu chứng | Cách xử lý |
|---|---|---|---|
| 1 | **Mất kết nối MySQL** | Backend không khởi động; log `Can't connect to MySQL server`, `Access denied for user`, `Unknown database` | Kiểm tra dịch vụ MySQL đã chạy (`net start MySQL`); đối chiếu `MYSQL_*` trong `.env`; kiểm tra `DATABASE_URL` (mã hoá URL ký tự đặc biệt trong mật khẩu); thử `mysql -u <user> -p -h <host> <db>` để cô lập lỗi; tạo database nếu chưa có |
| 2 | **Xung đột cổng (port in use)** | `[Errno 10048]` / `address already in use` khi chạy 8000 hoặc 5173 | `netstat -ano \| findstr :8000` để tìm PID → `taskkill /PID <PID> /F`; hoặc đổi cổng khi chạy và cập nhật `VITE_API_BASE_URL` + mở cổng mới trên tường lửa |
| 3 | **Token hết hạn (401)** | Bị đẩy về trang đăng nhập; API trả `401 Unauthorized` / `Could not validate credentials` | Đăng nhập lại. Tăng `JWT_EXPIRE_MINUTES` nếu cần phiên dài hơn. Đồng bộ giờ máy chủ (`w32tm /resync`). Lưu ý đổi `JWT_SECRET_KEY` sẽ vô hiệu mọi token cũ |
| 4 | **Phân quyền không khớp (403)** | API trả `403 Forbidden`; nút thao tác không hiện | Kiểm tra vai trò tài khoản; nội dung/kênh bậc MẬT cần cờ `clearance` hoặc `commander`/`admin`; Kênh Chỉ đạo cần cờ `directive_channel_access`; sửa/xoá nội dung người khác chỉ tác giả hoặc `commander`; **sau khi đổi quyền phải đăng xuất/đăng nhập lại** để token mang quyền mới |
| 5 | **Lỗi tải file dung lượng lớn** | Upload thất bại, báo `413` / "File quá lớn" | Tăng `MAX_UPLOAD_MB` trong `.env` rồi khởi động lại Backend; kiểm tra định dạng cho phép (`.pdf/.doc/.docx/.xls/.xlsx/.ppt/.pptx`, ảnh); nếu đặt sau reverse proxy thì nới `client_max_body_size` (Nginx) / `maxAllowedContentLength` (IIS); kiểm tra dung lượng trống ổ đĩa `storage/uploads/`; nén hoặc tách nhỏ tệp |
| 6 | **Máy trạm không mở được Cổng thông tin** | Trang trắng, không tải dữ liệu, lỗi CORS trong Console | Ping IP máy chủ; mở `http://<IP>:8000` để kiểm tra Backend + tường lửa (chế độ sản xuất phải thấy ngay giao diện); nếu còn chạy Frontend tách rời cổng 5173 thì kiểm tra `VITE_API_BASE_URL`; thêm origin máy trạm vào `EXTRA_CORS_ORIGINS` |
| 7 | **Mất điện / mất mạng LAN đột ngột khi đang soạn thảo** | Lo mất nội dung Chỉ thị/báo cáo/biên bản đang gõ dở | Đã có cơ chế tự động lưu bản nháp (mục 2.6.b) — mở lại đúng trang, nội dung tự khôi phục. Phía máy chủ: kiểm tra dịch vụ MySQL đã tự khởi động lại cùng Windows chưa, chạy lại `Chay_He_Thong.bat`; nếu nghi dữ liệu hỏng do tắt đột ngột, phục hồi từ bản sao lưu gần nhất (mục 4.6) |

### 4.6. Sao lưu và phục hồi dữ liệu định kỳ

- **Sao lưu tự động, đã nén:** `backend/scripts/backup_db.py` xuất toàn bộ CSDL `ludoan_db` ra file nén gzip (`.sql.gz`) tại `backend/storage/backups/`, đọc thông tin kết nối từ `.env` (mật khẩu không hiện trên dòng lệnh). Chạy tay:

  ```
  cd backend
  venv\Scripts\activate
  python scripts\backup_db.py
  ```

  Mỗi lần chạy tự động giữ lại 14 bản gần nhất (đổi bằng `--retention <số>`), xoá bớt bản cũ.

- **Đặt lịch chạy hằng ngày (Windows Task Scheduler):** tạo Basic Task chạy `Daily`, giờ thấp điểm; Action = *Start a program*, Program/script = `<đường dẫn dự án>\backend\venv\Scripts\python.exe`, Add arguments = `scripts\backup_db.py`, Start in = `<đường dẫn dự án>\backend`.

- **Phục hồi khi cần** (script tự hỏi xác nhận trước khi ghi đè):

  ```
  python scripts\backup_db.py --restore storage\backups\ludoan_db_20260830_231800.sql.gz
  ```

- **Sao lưu bổ sung tệp đính kèm:** định kỳ copy thư mục `backend/storage/uploads/` (tệp đính kèm/công văn) cùng `backend/storage/backups/` sang ổ đĩa/máy khác ngoài máy chủ chính — sao lưu tại chỗ không thay thế được sao lưu ngoài máy chủ (phòng máy chủ hỏng hoàn toàn).
- **Sau mỗi lần thay đổi API:** chạy `python scripts/export_openapi.py` để xuất lại `openapi.yaml`, ghi biên bản vào `openapi.CHANGELOG.md`, rồi mới cập nhật Frontend.
- **Kiểm thử hồi quy:** chạy `backend/scripts/test_full_system.py` trước khi đưa bản mới vào sử dụng.

---

## KẾT LUẬN VÀ KIẾN NGHỊ

Sáng kiến đã xây dựng thành công một Cổng thông tin nội bộ hoàn chỉnh cho Lữ đoàn Thông tin 21, số hoá đồng thời công tác tuyên truyền chính trị và luồng chỉ đạo – báo cáo – quản lý văn bản mật, vận hành hoàn toàn trong mạng nội bộ, do đơn vị làm chủ mã nguồn và dữ liệu. Phương pháp Vibecoding kết hợp trí tuệ nhân tạo cho phép một cá nhân hoàn thành khối lượng công việc lớn, chất lượng đồng đều, chi phí gần như bằng không.

**Kiến nghị:**

1. Cho phép triển khai chính thức trong toàn Lữ đoàn; bố trí 01–02 đồng chí phụ trách công nghệ thông tin tiếp nhận, vận hành theo tài liệu bàn giao.
2. Bố trí máy chủ đặt IP tĩnh, trang bị UPS (bộ lưu điện) tối thiểu; bật lịch sao lưu CSDL tự động hằng ngày (`backend/scripts/backup_db.py` qua Windows Task Scheduler) và định kỳ chuyển bản sao lưu ra ngoài máy chủ chính.
3. Nghiên cứu nhân rộng mô hình cho các đơn vị cùng cấp có điều kiện hạ tầng phù hợp.

---

*Tài liệu kèm theo: `openapi.yaml` (hợp đồng API), `openapi.CHANGELOG.md` (biên bản thay đổi), `docs/HUONG_DAN_SU_DUNG.docx` (hướng dẫn sử dụng có ảnh minh hoạ), mã nguồn `backend/` và `frontend/`.*

**Người báo cáo: Lê Văn Quỳnh – Đại đội 5, Lữ đoàn Thông tin 21, Bộ đội Biên phòng**
