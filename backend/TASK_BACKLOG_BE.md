# BACKEND TASK BACKLOG: E2E TESTING & CI/CD AUTOMATION

> **Vai trò:** Backend Lead Engineer  
> **Mục tiêu:** Bổ sung kịch bản E2E test cho các phân hệ nội dung còn lại và thiết lập pipeline CI/CD tự động.

---

## 1. Task BE-01: Viết E2E Test cho các Content Modules
- **File tạo mới:** `scripts/test_content_modules.py`
- **Yêu cầu kỹ thuật:**
  1. Kế thừa chuẩn kiểm thử từ `scripts/test_full_system.py` (chạy qua HTTP client tới Uvicorn thật + MySQL thật, tự dọn dẹp dữ liệu sau test).
  2. Viết test case phủ đủ các route trong `app/api/routes/`:
     - `posts.py` (Tin bài): Tạo, duyệt/xuất bản, phân quyền xem, xóa.
     - `announcements.py` (Thông báo): Tạo, ghim, hết hạn.
     - `documents.py` (Tài liệu / Công văn): Tải lên, tải về, phân quyền xem.
     - `education_materials.py` (Tài liệu giáo dục).
     - `home.py` (Dữ liệu tổng hợp trang chủ).

---

## 2. Task BE-02: Cấu hình kịch bản tự động hóa (CI/CD)
- **File tạo mới:** `.github/workflows/backend-ci.yml` (hoặc script kiểm thử tích hợp `scripts/run_all_tests.py`)
- **Yêu cầu kỹ thuật:**
  1. Tự động chạy tuần tự:
     - `python -m scripts.test_post_rbac`
     - `python -m scripts.test_full_system`
     - `python -m scripts.test_content_modules`
  2. Báo lỗi và dừng quy trình nếu có bất kỳ test case nào thất bại.

---

## Tiêu chuẩn nghiệm thu (Definition of Done)
- [ ] File `scripts/test_content_modules.py` chạy độc lập, pass 100% test case.
- [ ] Toàn bộ dữ liệu sinh ra trong quá trình test được tự động xóa sạch khỏi MySQL.