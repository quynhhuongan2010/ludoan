from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class EducationMaterial(Base):
    __tablename__ = "education_materials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    period_label = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    author = relationship("User")
