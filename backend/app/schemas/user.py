from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["soldier", "officer", "commander", "admin"]


class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., max_length=100)
    role: str = Field(default="soldier", max_length=50)
    unit_id: Optional[int] = None
    directive_channel_access: bool = False
    command_channel_access: bool = False


class RegisterRequest(BaseModel):
    """Nguoi dung tu dang ky o giao dien ngoai. Luon tao role=soldier, cho commander kich hoat."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., max_length=100)


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
    role: str
    is_active: bool
    clearance: bool
    unit_id: Optional[int]
    unit_name: Optional[str] = None
    directive_channel_access: bool
    command_channel_access: bool
    is_system: bool
    must_change_password: bool

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    full_name: str = Field(..., max_length=100)


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
