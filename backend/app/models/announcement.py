from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    # thap | binh_thuong | cao | khan
    priority = Column(String(20), nullable=False, server_default="binh_thuong", index=True)
    is_pinned = Column(Boolean, nullable=False, server_default="0", index=True)
    is_public = Column(Boolean, nullable=False, server_default="0", index=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    author = relationship("User")
