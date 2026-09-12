from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class DutySchedule(Base):
    """Mot dong ca truc trong 'bang truc tuan' cua don vi (xem DutyWeekPlan).

    Vong doi cua dong ca truc gan chat voi bang cha: chi them/sua/xoa duoc khi
    bang o trang thai `nhap`/`tra_lai`. `unit_id` sao chep tu `week_plan.unit_id`
    de truy van bang tong hop theo ngay khong phai join qua bang cha.
    """

    __tablename__ = "duty_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    week_plan_id = Column(
        Integer, ForeignKey("duty_week_plans.id"), nullable=True, index=True
    )
    duty_date = Column(Date, nullable=False, index=True)
    # Don vi dam nhiem ca truc (= week_plan.unit_id). Nullable o tang DB de tuong
    # thich ban ghi cu; dong tao moi luon co unit_id.
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True, index=True)
    # Nhom cuong vi truc - xem DUTY_TYPE_LABELS trong app/schemas/duty_schedule.py
    duty_type = Column(String(30), nullable=False, server_default="khac", index=True)
    shift = Column(String(50), nullable=False)  # VD "Ca ngay 06:00-18:00"
    duty_officer = Column(String(100), nullable=False)  # ho ten nguoi truc
    role_title = Column(String(100), nullable=False)  # chuc trach chi tiet
    contact_phone = Column(String(30), nullable=True)  # SDT vi tri truc (de dieu hanh)
    personnel_present = Column(Integer, nullable=True)  # quan so co mat
    personnel_total = Column(Integer, nullable=True)  # tong quan so bien che vi tri truc
    note = Column(String(500), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    author = relationship("User")
    unit = relationship("Unit")
    week_plan = relationship("DutyWeekPlan", back_populates="entries")
