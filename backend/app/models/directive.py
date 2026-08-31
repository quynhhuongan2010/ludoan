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


class Directive(Base):
    __tablename__ = "directives"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    # nhap = ban nhap (chi commander thay); da_ban_hanh = da pho bien toi don vi
    status = Column(String(20), nullable=False, server_default="nhap", index=True)
    # Bac truy cap: cong_khai | noi_bo | mat (chi thi trien khai mat/gap dat "mat")
    classification = Column(String(20), nullable=False, server_default="noi_bo", index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    author = relationship("User")
    acknowledgements = relationship(
        "DirectiveAcknowledgement",
        back_populates="directive",
        cascade="all, delete-orphan",
    )


class DirectiveAcknowledgement(Base):
    __tablename__ = "directive_acknowledgements"
    __table_args__ = (
        UniqueConstraint("directive_id", "user_id", name="uq_directive_user_ack"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    directive_id = Column(Integer, ForeignKey("directives.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=False, server_default=func.now())

    directive = relationship("Directive", back_populates="acknowledgements")
    user = relationship("User")
