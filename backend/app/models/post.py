from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    cover_image_url = Column(String(500), nullable=True)
    # Luong duyet bai: cho_duyet -> da_duyet / tra_lai
    status = Column(String(20), nullable=False, server_default="cho_duyet", index=True)
    review_note = Column(String(500), nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    # Bac truy cap: cong_khai | noi_bo | mat
    classification = Column(String(20), nullable=False, server_default="noi_bo", index=True)
    # Ghim len trang cong khai ("tin noi bat hang ngay")
    is_featured = Column(Boolean, nullable=False, server_default="0", index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    author = relationship("User", foreign_keys=[author_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
