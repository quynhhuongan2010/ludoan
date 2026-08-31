---
name: fast-api-mysql-auto-schema
description: Tự động khởi tạo cấu trúc bảng MySQL, Pydantic Schema và các endpoint CRUD trong dự án FastAPI theo cấu trúc phân tầng chuẩn.
version: 1.2.0
license: MIT
metadata:
  author: AI-Developer-Assistant
  mcp-server: mysql-manager  # Tuỳ chọn: nếu MCP server này đã được kết nối trong phiên làm việc, ưu tiên dùng nó để kiểm tra/quản lý bảng MySQL trực tiếp thay vì script Python thủ công. Nếu chưa kết nối, bỏ qua và dùng cách kiểm tra ở Bước 5.
---

# SKILL: Fast API + MySQL Auto-Schema

## Mục tiêu
Tự động hóa việc tạo bảng MySQL, Pydantic Schemas, SQLAlchemy Models và các endpoint CRUD liên quan trong dự án FastAPI dựa trên yêu cầu người dùng, đảm bảo tính nhất quán giữa cơ sở dữ liệu và API contract.

## Quy trình làm việc (Workflow)

### Bước 1: Phân tích yêu cầu (Input Analysis)
- Xác định rõ tên thực thể dữ liệu, các trường (fields), kiểu dữ liệu và ràng buộc (Primary Key, Foreign Key, Nullable, Default, Unique).

### Bước 2: Tạo Model & Schema (Layered Implementation)
- **Model (`app/models/<entity>.py`):** Kế thừa `Base` từ `app.core.database`, định nghĩa `__tablename__`, kiểu dữ liệu và ràng buộc.
- **Schema (`app/schemas/<entity>.py`):** Tạo tối thiểu 2 schema Pydantic:
  - `<Entity>Create`: Chứa các trường cần khi thêm mới/cập nhật.
  - `<Entity>Out`: Kế thừa hoặc mở rộng từ Create, bổ sung `id`, cấu hình `from_attributes = True`.

### Bước 3: Triển khai CRUD Router (`app/api/routes/<entity>s.py`)
- Định nghĩa router với prefix chuẩn (ví dụ `/items`, `/products`).
- Sử dụng `Depends(get_db)` để quản lý Session kết nối database an toàn.
- Viết đủ 5 endpoint chuẩn RESTful:
  - `POST /` (status 201): Tạo mới.
  - `GET /` (status 200): Lấy danh sách (có hỗ trợ phân trang).
  - `GET /{id}` (status 200, trả 404 nếu không tìm thấy).
  - `PUT /{id}` (status 200, cập nhật dữ liệu).
  - `DELETE /{id}` (status 204, xóa bản ghi).

### Bước 4: Đăng ký Router (`app/main.py`)
- Import và đăng ký router vào `app/main.py` bằng `app.include_router()`.
- Tuyệt đối không xóa hoặc ghi đè các router cũ đã tồn tại.

### Bước 5: Khởi tạo bảng & Kiểm tra (Validation)
- Đảm bảo cơ chế tự động tạo bảng hoạt động (`Base.metadata.create_all(bind=engine)` trong môi trường phát triển).
- `create_all` đã tự kiểm tra bảng tồn tại trước khi tạo (checkfirst mặc định) — không tự viết `DROP TABLE` hay `CREATE TABLE` thủ công đè lên cơ chế này để tránh lỗi `Table already exists` hoặc mất dữ liệu.
- Báo cáo rõ theo mẫu: "Bảng [table_name] đã được tạo/xác nhận thành công" kèm danh sách endpoint vừa thêm và schema tương ứng; nếu lỗi: "Lỗi xảy ra: [error_message chi tiết từ MySQL]".

## Nguyên tắc thiết kế bắt buộc (Best Practices)
1. **Bảo mật & Cấu hình:** Đọc toàn bộ biến kết nối MySQL từ `app/core/config.py` (file `.env`). Tuyệt đối không hardcode mật khẩu, host, user.
2. **Hỗ trợ tiếng Việt:** Mọi bảng và cột chuỗi phải tương thích với bộ mã `utf8mb4`.
3. **CORS:** Duy trì cấu hình CORS cho Frontend (`allow_origins=["http://localhost:5173"]`).
4. **Mã lỗi HTTP:** Trả đúng mã HTTP chuẩn: 200, 201, 204, 400, 404, 409 (nếu trùng lặp), 422 (sai dữ liệu đầu vào), 500 (lỗi máy chủ).

## Xử lý lỗi (Error Handling)
Khi triển khai Bước 3-5 gặp lỗi, phân loại và xử lý theo đúng nhóm sau, luôn báo lỗi gốc từ MySQL/SQLAlchemy cho người dùng thay vì nuốt lỗi:
1. **Lỗi kết nối (connection):** ví dụ `Access denied`, `Can't connect to MySQL server`. Kiểm tra: (a) service MySQL đang chạy, (b) `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE` trong `.env` đúng, (c) user MySQL đã được `GRANT` quyền trên đúng database. Không tự ý đổi mật khẩu hay tạo lại user trong MySQL — luôn hỏi/hướng dẫn người dùng tự chạy lệnh `CREATE USER`/`GRANT` với tài khoản admin của họ, trừ khi họ chủ động cung cấp thông tin admin và yêu cầu làm thay.
2. **Lỗi cú pháp/kiểu dữ liệu (schema mismatch):** đối chiếu lại kiểu cột trong Model (`String(255)`, `Integer`, ...) với ràng buộc thực tế của MySQL (độ dài, NOT NULL, UNIQUE) trước khi báo lỗi là "đã xong".
3. **Lỗi trùng lặp/khác cấu trúc (bảng đã tồn tại nhưng khác Model hiện tại):** KHÔNG tự ý `DROP TABLE` hay `ALTER TABLE` để "sửa cho khớp". Phải dừng lại, mô tả rõ điểm khác biệt, và hỏi người dùng chọn: xoá tạo lại (mất dữ liệu) hay viết migration (`ALTER TABLE`/Alembic) giữ dữ liệu.

## Cấu trúc thư mục chuẩn phải tuân thủ
```text
backend/
├── app/
│   ├── api/
│   │   └── routes/         # Khai báo các endpoint CRUD
│   ├── core/               # config.py, database.py (SessionLocal, Base)
│   ├── models/             # SQLAlchemy models (mô tả bảng MySQL)
│   ├── schemas/            # Pydantic schemas (validation dữ liệu vào/ra)
│   ├── services/           # Xử lý logic nghiệp vụ
│   ├── repositories/       # Truy vấn database
│   └── main.py             # Điểm khởi động FastAPI và đăng ký router
├── .env
├── .gitignore
└── requirements.txt