from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DutyShiftHandover(Base):
    """Biên bản bàn giao ca trực & Sổ nhật ký kíp trực điện tử (Step 5 - v7.5.0).

    Gắn liền với một dòng ca trực (DutySchedule).
    Quy trình:
      1. Ca trước (Giver) lập biên bản: quân số, khí tài thông tin, sự vụ, việc dở dang.
      2. Ca sau (Receiver) đối soát thực tế và ký nhận điện tử (da_nhan / co_kien_nghi).
      3. Cấp Chỉ huy (Commander) kiểm tra và ghi ý kiến chỉ đạo.
    """

    __tablename__ = "duty_shift_handovers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    schedule_id = Column(
        Integer, ForeignKey("duty_schedules.id"), nullable=False, index=True
    )

    giver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    giver_name = Column(String(100), nullable=False)

    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    receiver_name = Column(String(100), nullable=True)

    handover_time = Column(DateTime, nullable=False, server_default=func.now())

    personnel_report = Column(Text, nullable=True)
    equipment_status = Column(Text, nullable=True)
    incident_log = Column(Text, nullable=True)
    pending_tasks = Column(Text, nullable=True)
    commander_note = Column(Text, nullable=True)

    # cho_nhan | da_nhan | co_kien_nghi
    status = Column(String(30), nullable=False, server_default="cho_nhan", index=True)
    receiver_note = Column(String(500), nullable=True)

    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    schedule = relationship("DutySchedule")
    giver = relationship("User", foreign_keys=[giver_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
