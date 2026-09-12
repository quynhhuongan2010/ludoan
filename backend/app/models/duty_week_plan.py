from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DutyWeekPlan(Base):
    """Bang truc tuan cua mot don vi - don vi lap & trinh, chi huy phe duyet hang tuan.

    Luong trang thai (giong luong duyet `posts`):
        nhap -> cho_duyet -> da_duyet / tra_lai
    Chi bang `da_duyet` moi len bang tong hop toan Lu doan cho moi tai khoan;
    chi huy Lu doan (`commander`/`admin`) xem duoc moi trang thai de don doc.
    Moi don vi chi co 1 bang cho moi tuan (UNIQUE unit_id + week_start).
    """

    __tablename__ = "duty_week_plans"
    __table_args__ = (
        UniqueConstraint("unit_id", "week_start", name="uq_duty_week_plan_unit_week"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)  # luon la Thu Hai (ISO)
    # nhap | cho_duyet | da_duyet | tra_lai
    status = Column(String(20), nullable=False, server_default="nhap", index=True)
    note = Column(String(500), nullable=True)  # ghi chu chung cua ca bang
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(String(500), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    unit = relationship("Unit")
    author = relationship("User", foreign_keys=[author_id])
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    entries = relationship(
        "DutySchedule",
        back_populates="week_plan",
        cascade="all, delete-orphan",
        order_by="DutySchedule.duty_date, DutySchedule.duty_type, DutySchedule.id",
    )
    attachments = relationship(
        "DutyPlanAttachment",
        back_populates="week_plan",
        cascade="all, delete-orphan",
        order_by="DutyPlanAttachment.created_at, DutyPlanAttachment.id",
    )
