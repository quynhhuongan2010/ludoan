"""Module phan quyen nghiep vu theo Khoi/Nganh co quan & Ma tran quyen quan su (v7.6.0).

Co cau to chuc chuan:
- Khoi Tham muu (Phong Tham muu): Tac chien, Huan luyen, Thong tin, Co yeu, Lich truc & Kip truc.
- Khoi Chinh tri (Phong Chinh tri): CTD-CTCT, Giao duc truyen thong, Tuyen huan, Bao ve an ninh.
- Khoi Hau can - Ky thuat (Phong Hau can - Ky thuat): Quan nhu, Quan y, Khi tai TTLL, Doanh trai, Xe may.
- Toan Lu doan: Ban chi huy Lu doan (role 1, 2), Cap uy Lu doan, Quan tri he thong (role 0).
- Don vi co so: Tieu doan, Dai doi, Tram truc thuoc.
"""

from typing import Any, Dict
from app.core.roles import (
    ROLE_ADMIN,
    ROLE_LU_TRUONG,
    ROLE_LU_PHO,
    ROLE_CHI_HUY_DON_VI,
    ROLE_CA_NHAN,
    ROLE_NGUOI_DUNG,
    is_admin,
    is_command,
    can_post_content,
    can_manage_documents,
)

BRANCH_TOAN_LU_DOAN = "toan_lu_doan"
BRANCH_THAM_MUU = "tham_muu"
BRANCH_CHINH_TRI = "chinh_tri"
BRANCH_HAU_CAN_KY_THUAT = "hau_can_ky_thuat"
BRANCH_DON_VI_CO_SO = "don_vi_co_so"

BRANCH_LABELS = {
    BRANCH_TOAN_LU_DOAN: "Ban Chỉ huy Lữ đoàn & Quản trị hệ thống",
    BRANCH_THAM_MUU: "Khối Tham mưu (Tác chiến · Huấn luyện · TTLL)",
    BRANCH_CHINH_TRI: "Khối Chính trị (CTĐ-CTCT · Tuyên huấn · Giáo dục)",
    BRANCH_HAU_CAN_KY_THUAT: "Khối Hậu cần – Kỹ thuật (Trang bị VKTB · Vật tư)",
    BRANCH_DON_VI_CO_SO: "Đơn vị cơ sở (Tiểu đoàn · Đại đội · Trạm)",
}


def get_user_branch(user) -> str:
    """Xac dinh Khoi/Nganh co quan cua user dua vao role va don vi truc thuoc."""
    if user is None:
        return BRANCH_DON_VI_CO_SO

    # 1. Quan tri he thong hoac Chi huy Lu doan (Lữ trưởng, Chính uỷ, Lữ phó, Phó chính uỷ)
    role = getattr(user, "role", ROLE_NGUOI_DUNG)
    if role in (ROLE_ADMIN, ROLE_LU_TRUONG, ROLE_LU_PHO):
        return BRANCH_TOAN_LU_DOAN

    unit = getattr(user, "unit", None)
    if not unit:
        return BRANCH_DON_VI_CO_SO

    unit_name = (getattr(unit, "name", "") or "").lower()
    unit_kind = getattr(unit, "unit_kind", "") or ""

    if unit_kind in ("bch_lu_doan", "cap_uy"):
        return BRANCH_TOAN_LU_DOAN

    if "tham mưu" in unit_name:
        return BRANCH_THAM_MUU
    elif "chính trị" in unit_name:
        return BRANCH_CHINH_TRI
    elif "hậu cần" in unit_name or "kỹ thuật" in unit_name:
        return BRANCH_HAU_CAN_KY_THUAT
    elif unit_kind in ("tieu_doan", "dai_doi", "tram"):
        return BRANCH_DON_VI_CO_SO

    return BRANCH_DON_VI_CO_SO


def can_manage_branch(user, target_branch: str) -> bool:
    """Kiem tra quyen quan ly noi dung / nghiep vu cua mot Khoi/Nganh cu the.

    Chi huy cap Lu doan (role 0, 1, 2) toan quyen tren moi khoi.
    Can bo/chi huy cua khoi nao thi co quyen tren khoi do (role <= 4).
    """
    if user is None:
        return False

    role = getattr(user, "role", ROLE_NGUOI_DUNG)
    if role in (ROLE_ADMIN, ROLE_LU_TRUONG, ROLE_LU_PHO):
        return True

    user_branch = get_user_branch(user)
    if user_branch == BRANCH_TOAN_LU_DOAN:
        return True

    # Neu cung khoi va co quyen tu ca nhan tro len (role <= 4)
    if user_branch == target_branch and role <= ROLE_CA_NHAN:
        return True

    return False


def can_review_duty(user, unit_id: int | None = None) -> bool:
    """Quyen duyet bieu truc / kip truc:

    - Chi huy Lu doan (role 0..2) hoac Can bo Phong Tham muu (role <= 3): duyet toan Lu doan.
    - Chi huy don vi (role 3): duyet trong pham vi don vi cua minh.
    """
    if user is None:
        return False

    role = getattr(user, "role", ROLE_NGUOI_DUNG)
    if role in (ROLE_ADMIN, ROLE_LU_TRUONG, ROLE_LU_PHO):
        return True

    user_branch = get_user_branch(user)
    if user_branch == BRANCH_THAM_MUU and role <= ROLE_CHI_HUY_DON_VI:
        return True

    if role == ROLE_CHI_HUY_DON_VI:
        if unit_id is None:
            return True
        return getattr(user, "unit_id", None) == unit_id

    return False


def can_manage_political_education(user) -> bool:
    """Quyen bien tap / duyet Tu lieu Giao duc truyen thong & Chinh tri:

    - Chi huy Lu doan (role 0..2)
    - Can bo Phong Chinh tri (role <= 4)
    """
    return can_manage_branch(user, BRANCH_CHINH_TRI)


def can_manage_technical_equipment(user) -> bool:
    """Quyen quan ly khi tai, trang bi VKTB, thiet bi TTLL:

    - Chi huy Lu doan (role 0..2)
    - Can bo Phong Hau can - Ky thuat (role <= 4)
    """
    return can_manage_branch(user, BRANCH_HAU_CAN_KY_THUAT)


def get_permission_matrix(user) -> Dict[str, Any]:
    """Xuat ma tran quyen han chi tiet cua User phuc vu Frontend."""
    if user is None:
        return {
            "role": ROLE_NGUOI_DUNG,
            "branch": BRANCH_DON_VI_CO_SO,
            "branch_label": BRANCH_LABELS[BRANCH_DON_VI_CO_SO],
            "permissions": {},
        }

    branch = get_user_branch(user)
    role = getattr(user, "role", ROLE_NGUOI_DUNG)

    perms = {
        # Quyen he thong & an ninh
        "is_admin": is_admin(user),
        "is_commander": is_command(user),
        "has_classified_clearance": bool(getattr(user, "clearance", False)),
        "access_command_channel": bool(getattr(user, "command_channel_access", False)),
        "access_directive_channel": bool(getattr(user, "directive_channel_access", False)),
        "view_audit_logs": role in (ROLE_ADMIN, ROLE_LU_TRUONG, ROLE_LU_PHO),
        # Quyen theo Khoi/Nganh
        "manage_tham_muu": can_manage_branch(user, BRANCH_THAM_MUU),
        "manage_chinh_tri": can_manage_branch(user, BRANCH_CHINH_TRI),
        "manage_hau_can_ky_thuat": can_manage_branch(user, BRANCH_HAU_CAN_KY_THUAT),
        # Quyen nghiep vu cu the
        "review_duty_schedule": can_review_duty(user),
        "create_duty_handover": role <= ROLE_CA_NHAN,
        "review_duty_handover": is_command(user),
        "publish_news": can_post_content(user),
        "manage_political_education": can_manage_political_education(user),
        "manage_documents": can_manage_documents(user),
        "manage_users": role in (ROLE_ADMIN, ROLE_LU_TRUONG, ROLE_LU_PHO),
    }

    return {
        "role": role,
        "branch": branch,
        "branch_label": BRANCH_LABELS.get(branch, branch),
        "permissions": perms,
    }
