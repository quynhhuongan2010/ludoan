from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.types import JSONText
from app.models.user import User


class ContactBook(Base):
    """Mot bo danh ba = mot lan nhap file (.xlsx / .csv).

    Cac bo tach rieng nhau, khong gop chung khi tra cuu. `column_headers` giu
    nguyen thu tu cot cua file goc de FE dung bang hien thi.
    """

    __tablename__ = "contact_books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    source_file_name = Column(String(255), nullable=True)
    column_headers = Column(JSONText, nullable=False)  # list[str]
    row_count = Column(Integer, nullable=False, server_default="0")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    created_by = relationship(User)
    contacts = relationship(
        "Contact",
        back_populates="book",
        cascade="all, delete-orphan",
        order_by="Contact.row_index",
    )


class Contact(Base):
    """Mot dong danh ba.

    Giu NGUYEN moi cot cua file trong `extra` (dict {header: value}) de hien thi
    day du; ngoai ra map sang vai truong chuan (`full_name`, `unit`, `position`,
    `phone`, `email`) de tra cuu nhanh. `search_blob` = noi tat ca gia tri
    (lowercase) phuc vu LIKE.
    """

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("contact_books.id"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False, server_default="0")
    full_name = Column(String(255), nullable=True)
    unit = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    extra = Column(JSONText, nullable=False)  # dict[str, str] - toan bo cot cua dong
    search_blob = Column(Text, nullable=False)

    book = relationship("ContactBook", back_populates="contacts")
