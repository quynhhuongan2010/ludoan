from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class DutySchedule(Base):
    __tablename__ = "duty_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    duty_date = Column(Date, nullable=False, index=True)
    shift = Column(String(50), nullable=False)  # VD "Ca 1 (06:00-12:00)"
    duty_officer = Column(String(100), nullable=False)  # ho ten nguoi truc
    role_title = Column(String(100), nullable=False)  # chuc trach: "Truc chi huy", "Truc ban"...
    note = Column(String(500), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    author = relationship("User")
