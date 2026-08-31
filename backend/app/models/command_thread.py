from sqlalchemy import (
    Boolean,
    Column,
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


class CommandThread(Base):
    """Luong trao doi noi bo bao mat cao: Ban chi huy Lu doan + Cap uy / Dang bo.

    Khong phan pham vi theo don vi (moi thanh vien du quyen thay tat ca).
    Truy cap: `has_secret_clearance` (commander/admin HOAC clearance=True).
    """

    __tablename__ = "command_threads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    classification = Column(String(20), nullable=False, server_default="mat")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_message_at = Column(DateTime, nullable=True)
    is_closed = Column(Boolean, nullable=False, server_default="0", index=True)

    created_by = relationship(User)
    messages = relationship(
        "CommandMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="CommandMessage.created_at",
    )


class CommandMessage(Base):
    __tablename__ = "command_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("command_threads.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    attachment_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    thread = relationship("CommandThread", back_populates="messages")
    sender = relationship(User)


class CommandThreadRead(Base):
    __tablename__ = "command_thread_reads"
    __table_args__ = (
        UniqueConstraint("thread_id", "user_id", name="uq_command_thread_user_read"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("command_threads.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    last_read_message_id = Column(Integer, nullable=False, server_default="0")
    last_read_at = Column(DateTime, nullable=False, server_default=func.now())
