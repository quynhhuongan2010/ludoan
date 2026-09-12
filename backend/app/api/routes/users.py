from typing import Optional

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import (
    bootstrap_or_role,
    get_current_user,
    get_optional_user,
    require_roles,
)
from app.core.database import get_db
from app.core.roles import ADMIN_ROLES, COMMAND_ROLES, USER_DELETE_ROLES
from app.models.user import User
from app.schemas.user import (
    ChannelAccessUpdate,
    ClearanceUpdate,
    LoginRequest,
    PurgeResult,
    RegisterRequest,
    ResetPasswordRequest,
    RoleUpdate,
    Token,
    UnitAssignUpdate,
    UserCreate,
    UserInfoUpdate,
    UserImportResult,
    UserOut,
    UserPage,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(bootstrap_or_role(*COMMAND_ROLES))],
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    return user_service.create_user(db, user_in, current_user)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(reg_in: RegisterRequest, db: Session = Depends(get_db)):
    """Tu dang ky tai khoan tu giao dien ngoai. Tao role=5 (Nguoi dung), chua kich hoat."""
    return user_service.register_user(db, reg_in)


@router.get(
    "/",
    response_model=UserPage,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Danh sach nguoi dung, phan trang qua skip/limit. Tra ve {items, total, skip, limit}."""
    return user_service.list_users(db, skip, limit, active)


@router.post(
    "/import",
    response_model=UserImportResult,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)
async def import_users(
    file: UploadFile = File(..., description="File danh sách quân nhân (.xlsx, .xls hoặc .docx)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Nhập danh sách quân nhân hàng loạt từ file Excel (.xlsx, .xls) hoặc Word (.docx)."""
    file_bytes = await file.read()
    return user_service.import_users_from_file(
        db, file_bytes=file_bytes, filename=file.filename or "import.xlsx", current_user=current_user
    )


@router.get(
    "/import/template",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)
def get_user_import_template(
    format: str = Query("excel", pattern="^(excel|xlsx|word|docx)$", description="Định dạng file mẫu: excel hoặc word"),
):
    """Tải file mẫu Excel hoặc Word chuẩn quân sự để nhập danh sách quân nhân."""
    content, filename, media_type = user_service.generate_user_template(format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/purge-test-users",
    response_model=PurgeResult,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)
def purge_test_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xoá toàn bộ tài khoản thử nghiệm, chỉ giữ lại tài khoản admin."""
    return user_service.purge_test_users(db, current_user)


@router.get("/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return user_service.get_user_visible_to(db, user_id, current_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*USER_DELETE_ROLES))],
)
def delete_user(
    user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Xoa han tai khoan (role 0, 1, 2). Xem `user_service.delete_user` cho cac rang buoc."""
    user_service.delete_user(db, user_id, current_user)
    return None


@router.post(
    "/{user_id}/activate",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def activate_user(
    user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return user_service.set_user_active(db, user_id, True, current_user)


@router.post(
    "/{user_id}/deactivate",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def deactivate_user(
    user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return user_service.set_user_active(db, user_id, False, current_user)


@router.patch(
    "/{user_id}/clearance",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def set_clearance(
    user_id: int,
    payload: ClearanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.set_user_clearance(db, user_id, payload.clearance, current_user)


@router.patch(
    "/{user_id}/role",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def set_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.set_user_role(db, user_id, payload.role, current_user)


@router.patch(
    "/{user_id}/unit",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def set_unit(user_id: int, payload: UnitAssignUpdate, db: Session = Depends(get_db)):
    return user_service.set_user_unit(db, user_id, payload.unit_id)


@router.patch(
    "/{user_id}/info",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def set_info(user_id: int, payload: UserInfoUpdate, db: Session = Depends(get_db)):
    """Bo sung / sua Cap bac + Chuc danh cho mot tai khoan (bat buoc truoc khi kich hoat)."""
    return user_service.set_user_info(db, user_id, payload)


@router.patch(
    "/{user_id}/channel-access",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)
def set_channel_access(
    user_id: int,
    payload: ChannelAccessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.set_user_channel_access(db, user_id, payload, current_user)


@router.post(
    "/{user_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)
def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_service.reset_user_password(db, user_id, payload.new_password, current_user)
    return None


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    return user_service.authenticate(db, credentials, ip_address=ip_address)
