"""Chinh sach cap tai khoan & mat khau theo du an.

- Mat khau: >= 8 ky tu, co dong thoi chu cai va chu so.
- Username: 3-50 ky tu, chi gom [a-z0-9._-] (chu thuong).
- Tai khoan he thong (`User.is_system`) duoc MIEN quy tac nay - xem `user_service`.
"""

import re

from fastapi import HTTPException, status

MIN_PASSWORD_LENGTH = 8
USERNAME_PATTERN = re.compile(r"^[a-z0-9._-]{3,50}$")


def validate_password_strength(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Mật khẩu phải có ít nhất {MIN_PASSWORD_LENGTH} ký tự",
        )
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mật khẩu phải có cả chữ và số",
        )


def validate_username(username: str) -> None:
    if not USERNAME_PATTERN.match(username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tên đăng nhập chỉ gồm chữ thường, số và . _ - (3-50 ký tự)",
        )
