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
from app.models.unit import Unit
from app.models.user import User


class DirectiveThread(Base):
    """Luong trao doi 2 chieu giua Ban chi huy Lu doan va MOT don vi.

    Moi don vi co the co nhieu luong (theo chu de). BCH/admin thay tat ca;
    tai khoan don vi (co `directive_channel_access`) chi thay luong cua don vi minh.
    """

    __tablename__ = "directive_threads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_message_at = Column(DateTime, nullable=True)
    is_closed = Column(Boolean, nullable=False, server_default="0", index=True)

    unit = relationship(Unit)
    created_by = relationship(User)
    messages = relationship(
        "DirectiveMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="DirectiveMessage.created_at",
    )


class DirectiveMessage(Base):
    __tablename__ = "directive_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("directive_threads.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    attachment_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    thread = relationship("DirectiveThread", back_populates="messages")
    sender = relationship(User)


class DirectiveThreadRead(Base):
    __tablename__ = "directive_thread_reads"
    __table_args__ = (
        UniqueConstraint("thread_id", "user_id", name="uq_directive_thread_user_read"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("directive_threads.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # id tin nhan cuoi cung ma user da doc trong luong (chinh xac hon so voi moc thoi gian)
    last_read_message_id = Column(Integer, nullable=False, server_default="0")
    last_read_at = Column(DateTime, nullable=False, server_default=func.now())
