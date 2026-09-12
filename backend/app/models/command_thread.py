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
    members = relationship(
        "CommandThreadMember",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="CommandThreadMember.added_at",
    )
    documents = relationship(
        "CommandThreadDocument",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="CommandThreadDocument.created_at.desc()",
    )
    minutes_records = relationship(
        "CommandThreadMinutes",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="CommandThreadMinutes.generated_at.desc()",
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


class CommandThreadMember(Base):
    """Thanh phan duoc gan vao luong (gioi han quyen xem/nhan tin theo thanh vien).

    Nguoi tao luong luon duoc them lam thanh vien (xem `create_thread` o repository).
    `commander`/`admin` bo qua bang nay, luon thay moi luong (xem `command_thread_scope`).
    """

    __tablename__ = "command_thread_members"
    __table_args__ = (
        UniqueConstraint("thread_id", "user_id", name="uq_command_thread_member"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("command_threads.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    added_at = Column(DateTime, nullable=False, server_default=func.now())

    thread = relationship("CommandThread", back_populates="members")
    user = relationship(User)


class CommandThreadDocument(Base):
    """Kho van ban rieng cua luong (tach khoi dong tin nhan) - cong van chung/rieng.

    `visibility`: "chung" (moi thanh vien cua luong xem duoc) | "rieng" (chi nguoi
    tai len + commander/admin xem duoc) - loc o service, khong loc o day.
    """

    __tablename__ = "command_thread_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("command_threads.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    visibility = Column(String(10), nullable=False, server_default="chung")
    file_url = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False, server_default="0")
    content_type = Column(String(120), nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    thread = relationship("CommandThread", back_populates="documents")
    uploaded_by = relationship(User)


class CommandThreadMinutes(Base):
    """Bien ban thao luan - ghep tu dong tu lich su tin nhan (khong dung AI).

    Moi lan bam "Tao bien ban" sinh 1 ban ghi moi (giu lich su cac lan tao).
    """

    __tablename__ = "command_thread_minutes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(Integer, ForeignKey("command_threads.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    message_count = Column(Integer, nullable=False, server_default="0")
    generated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime, nullable=False, server_default=func.now())

    thread = relationship("CommandThread", back_populates="minutes_records")
    generated_by = relationship(User)


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
