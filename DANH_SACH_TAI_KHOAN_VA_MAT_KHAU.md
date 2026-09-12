# DANH SÁCH TÀI KHOẢN & MẬT KHẨU HỆ THỐNG
## Cổng thông tin điện tử nội bộ — Lữ đoàn Thông tin 21

> **Lưu ý bảo mật:** Tài liệu này lưu trữ nội bộ nhằm phục vụ quản trị viên theo dõi, bàn giao ca trực và hỗ trợ cán bộ, chiến sĩ khôi phục mật khẩu khi quên.

---

## 1. Danh sách tài khoản hiện có trong hệ thống

> **CSDL vừa được factory reset ngày 06/09/2026** (`scripts/factory_reset_db.py`) — toàn bộ dữ liệu nghiệp vụ và tài khoản đã bị xoá, chỉ còn lại **duy nhất tài khoản quản trị hệ thống** dưới đây và 11 đơn vị chuẩn. Quản trị viên đăng nhập rồi tự tạo lại các tài khoản (Quản lý người dùng) — bổ sung vào bảng này khi tạo.

| STT | Tên đăng nhập | Mật khẩu hiện tại | Họ và tên | Cấp bậc / Chức danh | Vai trò (Role) | Quyền hạn chính |
|:---:|:---|:---|:---|:---|:---|:---|
| **1** | `admin` | `admin` | Quản trị hệ thống | Quản trị viên kỹ thuật | **Role 0** (Quản trị hệ thống) | Toàn quyền cấu hình hệ thống, quản lý tài khoản, đơn vị, phân quyền, xem Nhật ký an ninh (Audit Trail). |

*Ghi chú: Đăng nhập lần đầu bằng `admin` / `admin`, hệ thống yêu cầu đổi mật khẩu mới (`must_change_password = True`). Tài khoản `admin` (`is_system`) được miễn quy tắc độ mạnh mật khẩu nhưng vẫn nên đặt mật khẩu khó đoán và giữ bí mật. Mọi tài khoản mới tạo/đặt lại mật khẩu cũng bị buộc đổi ở lần đăng nhập kế tiếp.*

---

## 2. Cách xử lý khi Quên mật khẩu hoặc cần Đặt lại mật khẩu

### Cách 1: Đặt lại mật khẩu nhanh bằng file `Dat_Lai_Mat_Khau.bat` (Khuyên dùng khi Admin quên mật khẩu)
Ở ngay thư mục gốc của phần mềm (`d:\Du_an_Lu_doan\ludoan-main`), có sẵn file công cụ:
👉 **[Dat_Lai_Mat_Khau.bat](file:///d:/Du_an_Lu_doan/ludoan-main/Dat_Lai_Mat_Khau.bat)**

1. Nháy đúp chuột vào file `Dat_Lai_Mat_Khau.bat`.
2. Màn hình sẽ hiển thị danh sách toàn bộ tài khoản trong cơ sở dữ liệu.
3. Nhập **Tên đăng nhập** cần đổi (ví dụ: `admin`).
4. Nhập **Mật khẩu mới** muốn đặt (ví dụ: `MatKhau@123`).
5. Bấm `Enter` -> Mật khẩu được cập nhật thành công ngay lập tức!

---

### Cách 2: Quản trị viên đặt lại mật khẩu trực tiếp trên Giao diện Web
*(Dành cho Quản trị viên khi cán bộ, chiến sĩ trong đơn vị quên mật khẩu)*

1. Đăng nhập vào hệ thống bằng tài khoản Quản trị (`admin`).
2. Trên thanh menu trên cùng, chọn **Quản trị** $\rightarrow$ **Quản lý người dùng** (hoặc truy cập đường dẫn [http://localhost:8000/quan-ly-nguoi-dung](http://localhost:8000/quan-ly-nguoi-dung)).
3. Tìm đến tài khoản của đồng chí cần đặt lại mật khẩu.
4. Nhấn vào biểu tượng **Chìa khóa** (`🔑`) ở cột Thao tác cuối dòng.
5. Nhập mật khẩu mới cho người dùng rồi bấm **Xác nhận**.
6. Thông báo cho người dùng mật khẩu mới; người dùng đăng nhập và đổi lại mật khẩu cá nhân.

---

### Cách 3: Đặt lại mật khẩu bằng dòng lệnh Terminal
Mở cửa sổ PowerShell hoặc Command Prompt tại thư mục `backend`:
```powershell
# Xem danh sách tài khoản
venv\Scripts\python.exe scripts/check_login.py

# Đặt lại mật khẩu cho tài khoản bất kỳ:
venv\Scripts\python.exe scripts/check_login.py --user <tên_đăng_nhập> --set-password "<mật_khẩu_mới>"

# Ví dụ đặt lại mật khẩu cho tài khoản admin thành MatKhauMoi@123:
venv\Scripts\python.exe scripts/check_login.py --user admin --set-password "MatKhauMoi@123"
```

---

## 3. Quy tắc đặt mật khẩu bảo mật quân đội
- Tối thiểu 8 ký tự.
- Khuyến khích kết hợp: Chữ hoa, chữ thường, chữ số và ký tự đặc biệt (ví dụ: `@`, `#`, `!`).
- Tránh đặt mật khẩu quá đơn giản như: `123456`, `password`, trùng hoàn toàn với tên đăng nhập.
- Tài khoản nhập sai quá 5 lần liên tiếp sẽ bị hệ thống **khóa tự động 15 phút** (cơ chế chống Brute-force).
