from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ContactBookOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    source_file_name: Optional[str]
    column_headers: list[str]
    row_count: int
    created_by_id: int
    created_by_full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContactOut(BaseModel):
    id: int
    book_id: int
    row_index: int
    full_name: Optional[str]
    unit: Optional[str]
    position: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    # Toan bo cac truong (cot) cua file danh ba goc — hien thi day du khi xem chi tiet.
    extra: dict[str, str]

    model_config = ConfigDict(from_attributes=True)


class ContactPage(BaseModel):
    """Ket qua phan trang cho GET /contact-books/{id}/contacts."""

    items: list[ContactOut]
    total: int
    skip: int
    limit: int
    # Thu tu cot goc — FE dung de render bang dong.
    columns: list[str]
