from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.roles import DEFAULT_CREATE_ROLE

# Vai tro luu bang so nguyen 0..5 (xem app/core/roles.py):
#   0 Quan tri he thong | 1 Lu truong - Chinh uy | 2 Lu pho - Pho chinh uy
#   3 Chi huy don vi     | 4 Ca nhan              | 5 Nguoi dung
Role = Literal[0, 1, 2, 3, 4, 5]


class UserCreate(BaseModel):
    """Tao tai khoan truc tiep (chi huy/admin). Chi cap cho can bo/QNCN da co bien che

    thuc te -> bat buoc ghi ro cap bac, chuc danh, don vi cong tac ngay khi tao.
    """

    username: str = Field(..., max_length=50)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., max_length=100)
    role: Role = Field(default=DEFAULT_CREATE_ROLE, description="Vai trò 0..5 (mặc định 4 = Cá nhân)")
    rank: str = Field(..., min_length=1, max_length=100, description="Cấp bậc quân hàm")
    position: str = Field(..., min_length=1, max_length=150, description="Chức danh công tác")
    unit_id: int = Field(..., description="Đơn vị làm việc - bắt buộc")
    directive_channel_access: bool = False
    command_channel_access: bool = False


class RegisterRequest(BaseModel):
    """Nguoi dung tu dang ky o giao dien ngoai. Luon tao role=5 (Nguoi dung), chua kich hoat.

    Cap bac / chuc danh / don vi se do chi huy bo sung (PATCH .../info, .../unit)
    truoc khi kich hoat duoc tai khoan - xem `user_service.set_user_active`.
    """

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., max_length=100)


class UserInfoUpdate(BaseModel):
    """Bo sung / sua cap bac + chuc danh cho mot tai khoan (chi huy/admin)."""

    rank: str = Field(..., min_length=1, max_length=100)
    position: str = Field(..., min_length=1, max_length=150)


class ClearanceUpdate(BaseModel):
    clearance: bool


class RoleUpdate(BaseModel):
    role: Role


class UnitAssignUpdate(BaseModel):
    unit_id: Optional[int] = None


class ChannelAccessUpdate(BaseModel):
    directive_channel_access: Optional[bool] = None
    command_channel_access: Optional[bool] = None


class ResetPasswordRequest(BaseModel):
    # Rang buoc do dai/do manh nam o service (tai khoan is_system duoc mien).
    new_password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: int
    role_label: str
    rank: Optional[str] = None
    position: Optional[str] = None
    is_active: bool
    clearance: bool
    unit_id: Optional[int]
    unit_name: Optional[str] = None
    directive_channel_access: bool
    command_channel_access: bool
    is_system: bool
    must_change_password: bool

    model_config = ConfigDict(from_attributes=True)


class UserPage(BaseModel):
    """Ket qua phan trang cho GET /users/."""

    items: list[UserOut]
    total: int
    skip: int
    limit: int


class ProfileUpdate(BaseModel):
    full_name: str = Field(..., max_length=100)


class UserPermissionsOut(BaseModel):
    user_id: int
    username: str
    full_name: str
    role: int
    role_label: str
    branch: str
    branch_label: str
    unit_id: Optional[int] = None
    unit_name: Optional[str] = None
    permissions: dict[str, bool]


class PasswordChange(BaseModel):
    current_password: str
    # Rang buoc do manh nam o service (tai khoan is_system duoc mien).
    new_password: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role = Field(
        ...,
        description=(
            "Vai trò của tài khoản vừa đăng nhập (số nguyên 0..5 — nguồn sự thật: "
            "app/core/roles.py). "
            "0 = Quản trị hệ thống (admin); "
            "1 = Lữ trưởng - Chính uỷ; "
            "2 = Lữ phó - Phó chính uỷ; "
            "3 = Chỉ huy các đơn vị; "
            "4 = Cá nhân; "
            "5 = Người dùng."
        ),
    )


class UserImportRowError(BaseModel):
    row_index: int
    username: Optional[str] = None
    error: str


class UserImportResult(BaseModel):
    total_rows: int
    success_count: int
    error_count: int
    errors: list[UserImportRowError] = []
    created_usernames: list[str] = []


class PurgeResult(BaseModel):
    purged_count: int
    message: str
