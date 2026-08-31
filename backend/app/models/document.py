from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # bieu_mau | huong_dan | quy_che_quy_dinh | ke_hoach | bao_cao | van_ban_chi_dao
    category = Column(String(30), nullable=False, index=True)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)  # ten goc khi tai len
    file_size = Column(Integer, nullable=False)  # bytes
    content_type = Column(String(100), nullable=False)
    # Bac truy cap: cong_khai | noi_bo | mat
    classification = Column(String(20), nullable=False, server_default="noi_bo", index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    uploaded_by = relationship("User")
