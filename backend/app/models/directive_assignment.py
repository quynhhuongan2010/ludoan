from sqlalchemy import (
    Column,
    Date,
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
from app.models.directive import Directive
from app.models.unit import Unit
from app.models.user import User


class DirectiveAssignment(Base):
    """Nhiem vu giao xuong don vi (co the gan voi mot Chi thi).

    Trang thai tong quan luu o `status` (chua_giao | dang_thuc_hien | hoan_thanh);
    `qua_han` la trang thai suy dien khi qua `due_date` ma chua hoan thanh.
    Chi `commander`/`admin` tao / sua / huy va duyet bao cao.
    """

    __tablename__ = "directive_assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    directive_id = Column(Integer, ForeignKey("directives.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, server_default="chua_giao", index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    directive = relationship(Directive)
    created_by = relationship(User)
    targets = relationship(
        "DirectiveAssignmentTarget",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="DirectiveAssignmentTarget.id",
    )


class DirectiveAssignmentTarget(Base):
    """Doi tuong duoc giao: mot don vi, tuy chon kem mot ca nhan phu trach."""

    __tablename__ = "directive_assignment_targets"
    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "unit_id", "assignee_id", name="uq_assignment_unit_assignee"
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assignment_id = Column(
        Integer, ForeignKey("directive_assignments.id"), nullable=False, index=True
    )
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    # chua_nop | cho_duyet | da_duyet | tra_lai
    status = Column(String(20), nullable=False, server_default="chua_nop", index=True)
    submitted_at = Column(DateTime, nullable=True)

    assignment = relationship("DirectiveAssignment", back_populates="targets")
    unit = relationship(Unit)
    assignee = relationship(User, foreign_keys=[assignee_id])
    submissions = relationship(
        "DirectiveSubmission",
        back_populates="target",
        cascade="all, delete-orphan",
        order_by="DirectiveSubmission.created_at",
    )


class DirectiveSubmission(Base):
    """Mot lan nop bao cao tien do cho mot target (co lich su nhieu lan)."""

    __tablename__ = "directive_submissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    target_id = Column(
        Integer, ForeignKey("directive_assignment_targets.id"), nullable=False, index=True
    )
    content = Column(Text, nullable=False)
    attachment_url = Column(String(255), nullable=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    # Ket qua duyet cua chi huy cho chinh lan nop nay
    review_result = Column(String(20), nullable=True)  # da_duyet | tra_lai
    review_note = Column(String(500), nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    target = relationship("DirectiveAssignmentTarget", back_populates="submissions")
    submitted_by = relationship(User, foreign_keys=[submitted_by_id])
    reviewed_by = relationship(User, foreign_keys=[reviewed_by_id])
