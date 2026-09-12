"""Vai tro tai khoan (`User.role`) - luu bang SO NGUYEN 0..5.

| gia tri | ten                       | nhom quyen                         |
|---------|---------------------------|------------------------------------|
| 0       | Quan tri he thong (admin) | doc quyen admin + toan quyen chi huy|
| 1       | Lu truong - Chinh uy      | toan quyen chi huy                 |
| 2       | Lu pho - Pho chinh uy     | toan quyen chi huy                 |
| 3       | Chi huy cac don vi        | toan quyen chi huy (chua gioi han theo don vi)|
| 4       | Ca nhan                   | dang/sua Tin tuc - Hoat dong + Giao duc chinh tri|
| 5       | Nguoi dung                | chi xem noi bo, khong dang bai     |

So do phan quyen "A": 0,1,2,3 = tuong duong role `commander`/`admin` cu;
4 = tuong duong `officer` cu; 5 = tai khoan da kich hoat nhung chi xem.
"""

ROLE_ADMIN = 0
ROLE_LU_TRUONG = 1
ROLE_LU_PHO = 2
ROLE_CHI_HUY_DON_VI = 3
ROLE_CA_NHAN = 4
ROLE_NGUOI_DUNG = 5

VALID_ROLES = (0, 1, 2, 3, 4, 5)

# Vai tro mac dinh khi TU dang ky (POST /users/register): thap nhat, chi xem.
DEFAULT_REGISTER_ROLE = ROLE_NGUOI_DUNG
# Vai tro mac dinh khi chi huy/admin tao truc tiep (UserCreate) neu khong chon.
DEFAULT_CREATE_ROLE = ROLE_CA_NHAN

# --- Nhom quyen (dung cho require_roles / kiem tra trong service) ---
# Tuong duong role `commander` cu: ban hanh chi thi, duyet/dang moi noi dung,
# quan ly tai khoan, vao kenh han che, xem/tao noi dung bac "mat".
COMMAND_ROLES = (ROLE_ADMIN, ROLE_LU_TRUONG, ROLE_LU_PHO, ROLE_CHI_HUY_DON_VI)
# Duoc dang / sua Tin tuc - Hoat dong + Giao duc chinh tri (tuong duong `officer` cu).
CONTENT_ROLES = COMMAND_ROLES + (ROLE_CA_NHAN,)
# Quan ly Van ban - Tai lieu - Bieu mau: chi Quan tri he thong (0),
# Lu truong - Chinh uy (1), Lu pho - Pho chinh uy (2). Chi huy don vi (3) va
# Ca nhan (4) chi duoc xem / tai ve.
DOCUMENT_MANAGE_ROLES = (ROLE_ADMIN, ROLE_LU_TRUONG, ROLE_LU_PHO)
# Duoc xoa han tai khoan (DELETE /users/{id}): Quan tri he thong (0),
# Lu truong - Chinh uy (1), Lu pho - Pho chinh uy (2). Chi huy don vi (3) chi
# duoc khoa (deactivate) chu khong xoa.
USER_DELETE_ROLES = (ROLE_ADMIN, ROLE_LU_TRUONG, ROLE_LU_PHO)
# Tai khoan cap chi huy tu Lu pho tro len (0, 1, 2) KHONG bao gio bi xoa qua
# DELETE /users/{id} (phai ha quyen hoac khoa) - bao ve du lai lich su chi huy.
USER_UNDELETABLE_ROLES = (ROLE_ADMIN, ROLE_LU_TRUONG, ROLE_LU_PHO)
# Doc quyen quan tri he thong.
ADMIN_ROLES = (ROLE_ADMIN,)
# Duoc DUYET nhom chat (POST /chats/{id}/review): Quan tri he thong (0),
# Lu truong - Chinh uy (1). Nhom do role 4..5 tao phai cho nhom nay duyet.
CHAT_GROUP_APPROVE_ROLES = (ROLE_ADMIN, ROLE_LU_TRUONG)

ROLE_LABELS = {
    ROLE_ADMIN: "Quản trị hệ thống",
    ROLE_LU_TRUONG: "Lữ trưởng - Chính uỷ",
    ROLE_LU_PHO: "Lữ phó - Phó chính uỷ",
    ROLE_CHI_HUY_DON_VI: "Chỉ huy đơn vị",
    ROLE_CA_NHAN: "Cá nhân",
    ROLE_NGUOI_DUNG: "Người dùng",
}


def coerce_role(value) -> int | None:
    """Ep `value` (int / str so / None) ve int vai tro; None neu khong hop le."""
    if value is None or isinstance(value, bool):
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n in VALID_ROLES else None


def role_label(value) -> str:
    n = coerce_role(value)
    return ROLE_LABELS.get(n, str(value))


def _role_of(user) -> int | None:
    if user is None:
        return None
    return coerce_role(getattr(user, "role", None))


def is_admin(user) -> bool:
    """Doc quyen quan tri he thong (role 0)."""
    return _role_of(user) in ADMIN_ROLES


def is_command(user) -> bool:
    """Bac chi huy day du - tuong duong role `commander`/`admin` cu (role 0..3)."""
    return _role_of(user) in COMMAND_ROLES


def can_post_content(user) -> bool:
    """Duoc dang / sua Tin tuc - Hoat dong + Giao duc chinh tri (role 0..4)."""
    return _role_of(user) in CONTENT_ROLES


def can_manage_documents(user) -> bool:
    """Duoc tao / sua / xoa Van ban - Tai lieu - Bieu mau (chi role 0, 1, 2)."""
    return _role_of(user) in DOCUMENT_MANAGE_ROLES


def can_approve_chat_group(user) -> bool:
    """Duoc duyet / tu choi nhom chat cho duyet (role 0, 1)."""
    return _role_of(user) in CHAT_GROUP_APPROVE_ROLES
