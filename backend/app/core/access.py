"""Phan loai noi dung theo bac truy cap + tien ich kiem tra quyen xem.

3 muc:
  - cong_khai : ai cung xem duoc (ke ca khach chua dang nhap)
  - noi_bo    : moi tai khoan da kich hoat
  - mat       : chi commander HOAC user duoc cap quyen (User.clearance = True)
"""

from typing import Optional

from app.core.roles import is_command

CLASSIFICATIONS = ("cong_khai", "noi_bo", "mat")
DEFAULT_CLASSIFICATION = "noi_bo"


def has_secret_clearance(user) -> bool:
    if user is None:
        return False
    return is_command(user) or bool(getattr(user, "clearance", False))


def allowed_classifications(user) -> list[str]:
    """Danh sach muc phan loai ma `user` duoc phep xem (dung loc query danh sach)."""
    if user is None:
        return ["cong_khai"]
    if has_secret_clearance(user):
        return ["cong_khai", "noi_bo", "mat"]
    return ["cong_khai", "noi_bo"]


def can_view_classification(classification: str, user: Optional[object]) -> bool:
    if classification == "cong_khai":
        return True
    if user is None:
        return False
    if classification == "mat":
        return has_secret_clearance(user)
    return True  # noi_bo


# --- Kenh han che: cap quyen bang co tren tung User (khong theo don vi) ---

def is_command_level(user) -> bool:
    """Bac chi huy day du (vai tro 0..3) - tuong duong `commander`/`admin` cu."""
    return is_command(user)


def can_access_directive_channel(user) -> bool:
    """Kenh Chi dao - Bao cao (BCH <-> don vi)."""
    return is_command_level(user) or bool(getattr(user, "directive_channel_access", False))


def can_access_command_channel(user) -> bool:
    """Kenh chuyen BCH Lu doan + Cap uy / Dang bo (bao mat cao).

    Yeu cau nghiem ngat: `commander`/`admin` HOAC `User.clearance = True`
    (dung `has_secret_clearance`). Khong dung co `command_channel_access` nua.
    """
    return has_secret_clearance(user) or is_command_level(user)


def command_thread_scope(user) -> str | None:
    """Pham vi luong `Kenh chuyen BCH & Cap uy` (`command_threads`) ma `user` duoc xem.

    - `"all"`    : BCH/admin - thay moi luong bat ke co duoc gan lam thanh vien hay khong.
    - `"member"` : chi thay luong da duoc gan lam thanh vien (bang `command_thread_members`).
    - `None`     : khong co quyen vao kenh (thieu `has_secret_clearance`).
    """
    if not can_access_command_channel(user):
        return None
    return "all" if is_command_level(user) else "member"


def directive_thread_scope(user):
    """Pham vi luong Chi dao - Bao cao ma `user` duoc xem.

    - `"all"`  : xem moi luong cua moi don vi (BCH/admin, hoac tai khoan co quyen kenh
                 dang thuoc don vi loai `bch_lu_doan`).
    - `int`    : chi xem luong cua dung don vi id nay (tai khoan don vi cap duoi).
    - `None`   : khong co quyen vao kenh.
    """
    if not can_access_directive_channel(user):
        return None
    if is_command_level(user):
        return "all"
    unit = getattr(user, "unit", None)
    if unit is not None and getattr(unit, "unit_kind", None) == "bch_lu_doan":
        return "all"
    return user.unit_id
