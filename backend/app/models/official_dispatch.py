from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import User


class OfficialDispatch(Base):
    """So quan ly Cong van / Van ban di - den (mat noi bo).

    `direction`: `di` (van ban di) | `den` (van ban den).
    `status`   : `moi` | `dang_xu_ly` | `da_xu_ly` | `luu_tru`.
    """

    __tablename__ = "official_dispatches"
    __table_args__ = (
        UniqueConstraint("direction", "dispatch_number", name="uq_dispatch_direction_number"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    direction = Column(String(10), nullable=False, server_default="den", index=True)
    dispatch_number = Column(String(80), nullable=False, index=True)
    summary = Column(String(500), nullable=False)  # trich yeu
    issuing_org = Column(String(200), nullable=True)  # co quan ban hanh
    receiving_org = Column(String(200), nullable=True)  # noi nhan
    issued_date = Column(Date, nullable=True)  # ngay ban hanh
    received_date = Column(Date, nullable=True)  # ngay den (van ban den)
    status = Column(String(20), nullable=False, server_default="moi", index=True)
    classification = Column(String(20), nullable=False, server_default="mat")
    note = Column(Text, nullable=True)
    attachment_url = Column(String(255), nullable=True)
    attachment_name = Column(String(255), nullable=True)
    content_type = Column(String(120), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    created_by = relationship(User)
    acknowledgements = relationship(
        "DispatchAcknowledgement",
        back_populates="dispatch",
        cascade="all, delete-orphan",
        order_by="DispatchAcknowledgement.acknowledged_at",
    )


class DispatchAcknowledgement(Base):
    """So ky nhan / theo doi quan triet cong van."""

    __tablename__ = "dispatch_acknowledgements"
    __table_args__ = (
        UniqueConstraint("dispatch_id", "user_id", name="uq_dispatch_user_ack"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dispatch_id = Column(
        Integer, ForeignKey("official_dispatches.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=False, server_default=func.now())
    response_note = Column(String(500), nullable=True)  # phan hoi thuc hien

    dispatch = relationship("OfficialDispatch", back_populates="acknowledgements")
    user = relationship(User)
