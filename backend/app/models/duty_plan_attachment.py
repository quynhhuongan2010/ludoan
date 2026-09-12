from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class DutyPlanAttachment(Base):
    """Tep dinh kem cua mot bang truc tuan (`duty_week_plans`).

    Moi bang truc co the dinh NHIEU tep, moi loai: ban PDF da ky, ban Excel,
    anh scan, phu luc quan so... Cho phep dinh kem o moi trang thai bang truc
    (ke ca sau khi da duyet - de gan ban ky).
    """

    __tablename__ = "duty_plan_attachments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    week_plan_id = Column(
        Integer,
        ForeignKey("duty_week_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # /static/duty-plans/<uuid>.<ext>
    file_url = Column(String(500), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False, server_default="0")
    content_type = Column(String(100), nullable=True)
    # Mo ta ngan tu nguoi tai len (vd "Ban da ky", "Phu luc quan so").
    label = Column(String(200), nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    week_plan = relationship("DutyWeekPlan", back_populates="attachments")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
