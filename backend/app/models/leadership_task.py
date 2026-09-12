"""Model Nhiem vu & Y kien chi dao cua Ban Chi huy Lu doan (v7.7.0).

Phan dinh ro 5 cuong vi lanh dao:
- lu_truong: Lu doan truong (Quan su, Tac chien, SSCĐ, Ke hoach)
- chinh_uy: Chinh uy Lu doan (CTĐ-CTCT, Can bo, Tuyen huan, Bao ve an ninh)
- lu_pho_tmt: Pho Lu doan truong kiem Tham muu truong (Tac chien, Huan luyen, TTLL)
- lu_pho_hckt: Pho Lu doan truong Hau can - Ky thuat (Trang bi VKTB, Khi tai, Hau can)
- pho_chinh_uy: Pho Chinh uy Lu doan (Chinh sach, Dan van, Quan chung)
"""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class LeadershipTask(Base):
    __tablename__ = "leadership_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Cuong vi chi dao: lu_truong | chinh_uy | lu_pho_tmt | lu_pho_hckt | pho_chinh_uy
    commander_role = Column(String(30), nullable=False, index=True)
    commander_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    commander_name = Column(String(120), nullable=False)

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # Khoi nghiep vu chu tri: tham_muu | chinh_tri | hau_can_ky_thuat | toan_lu_doan
    target_branch = Column(String(50), nullable=False, server_default="toan_lu_doan", index=True)

    # Don vi cu the chu tri thuc hien (neu co)
    assigned_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True, index=True)
    assigned_unit_name = Column(String(120), nullable=True)

    # Do khan: hoa_toc | khan | thuong
    urgency = Column(String(20), nullable=False, server_default="thuong", index=True)
    deadline = Column(Date, nullable=True)

    # Trang thai: dang_thuc_hien | da_bao_cao | da_hoan_thanh | can_bo_sung
    #   dang_thuc_hien -> (submit_report) da_bao_cao -> (review_task) da_hoan_thanh|can_bo_sung
    status = Column(String(30), nullable=False, server_default="dang_thuc_hien", index=True)

    # Bao cao ket qua tu don vi
    report_content = Column(Text, nullable=True)
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reported_by_name = Column(String(120), nullable=True)
    reported_at = Column(DateTime, nullable=True)

    # But phe / danh gia cua Chi huy sau khi don vi bao cao
    review_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    commander = relationship("User", foreign_keys=[commander_id])
    reported_by = relationship("User", foreign_keys=[reported_by_id])
    assigned_unit = relationship("Unit", foreign_keys=[assigned_unit_id])
