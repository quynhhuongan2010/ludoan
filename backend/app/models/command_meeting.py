from sqlalchemy import (
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


class CommandMeeting(Base):
    """Cuoc hop / giao ban truc tuyen cua Ban chi huy & Cap uy (bao mat cao).

    Khong tu dung ha tang video: `meeting_link` la duong dan phong hop ngoai.
    `status`: sap_dien_ra | dang_dien_ra | da_ket_thuc | da_huy.
    Truy cap: `has_secret_clearance` (commander/admin HOAC clearance=True).
    """

    __tablename__ = "command_meetings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)
    meeting_link = Column(String(500), nullable=True)
    agenda = Column(Text, nullable=True)
    minutes = Column(Text, nullable=True)
    attachment_url = Column(String(255), nullable=True)
    attachment_name = Column(String(255), nullable=True)
    content_type = Column(String(120), nullable=True)
    status = Column(String(20), nullable=False, server_default="sap_dien_ra", index=True)
    classification = Column(String(20), nullable=False, server_default="mat")
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    created_by = relationship(User)
    attendees = relationship(
        "CommandMeetingAttendee",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="CommandMeetingAttendee.id",
    )


class CommandMeetingAttendee(Base):
    """Thanh phan trieu tap + diem danh cua mot cuoc hop."""

    __tablename__ = "command_meeting_attendees"
    __table_args__ = (
        UniqueConstraint("meeting_id", "user_id", name="uq_meeting_user_attendee"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("command_meetings.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    # co_mat | vang_mat | chua_diem_danh
    attendance = Column(String(20), nullable=False, server_default="chua_diem_danh")
    absence_reason = Column(String(500), nullable=True)
    contribution_note = Column(Text, nullable=True)

    meeting = relationship("CommandMeeting", back_populates="attendees")
    user = relationship(User)
    unit = relationship(Unit)
