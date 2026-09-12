"""Kieu cot SQLAlchemy dung chung."""

import json

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator


class JSONText(TypeDecorator):
    """Luu du lieu JSON duoi dang cot TEXT (utf8mb4).

    Tranh quirk cua cot MySQL `JSON` + PyMySQL lam hong ky tu tieng Viet
    (charset ket noi khong phai utf8mb4 -> lone surrogate). Cot TEXT round-trip
    tieng Viet on dinh nhu moi module khac trong du an.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)):
            value = value.decode("utf-8")
        return json.loads(value)
