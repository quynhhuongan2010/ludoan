from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.unit import Unit


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="soldier")
    is_active = Column(Boolean, nullable=False, default=True)
    # Duoc commander cap quyen xem noi dung phan loai "mat"
    clearance = Column(Boolean, nullable=False, server_default="0")
    # Don vi (FK units.id) - admin gan; nullable vi tai khoan cu / khach he thong
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True, index=True)
    # Co truy cap 2 kenh han che - admin bat/tat tren tung tai khoan
    directive_channel_access = Column(Boolean, nullable=False, server_default="0")
    command_channel_access = Column(Boolean, nullable=False, server_default="0")
    # Tai khoan he thong (admin mac dinh) - khong the khoa / ha quyen / xoa
    is_system = Column(Boolean, nullable=False, server_default="0")
    # Buoc doi mat khau o lan dang nhap dau (tai khoan do admin cap / vua reset)
    must_change_password = Column(Boolean, nullable=False, server_default="0")

    unit = relationship(Unit, lazy="joined")

    @property
    def unit_name(self) -> str | None:
        return self.unit.name if self.unit is not None else None
