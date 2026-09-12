from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.roles import ROLE_NGUOI_DUNG, role_label
from app.models.unit import Unit


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    # Vai tro: so nguyen 0..5 (xem app/core/roles.py). Mac dinh 5 = "Nguoi dung".
    role = Column(Integer, nullable=False, default=ROLE_NGUOI_DUNG, server_default=str(ROLE_NGUOI_DUNG))
    # Cap bac quan ham (vd "Thieu ta", "Thuong uy QNCN") - o nhap tu do.
    # Cot DB dat ten "military_rank" vi "rank" la tu khoa dat trong MySQL 8
    # (ham window RANK()); thuoc tinh Python/schema van goi la `rank`.
    rank = Column("military_rank", String(100), nullable=True)
    # Chuc danh cong tac (vd "Tro ly Tham muu", "Dai doi truong").
    position = Column(String(150), nullable=True)
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

    @property
    def role_label(self) -> str:
        """Ten hien thi cua vai tro (vd "Lữ trưởng - Chính uỷ"). Phuc vu FE."""
        return role_label(self.role)
