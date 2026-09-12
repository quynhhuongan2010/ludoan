from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    # Nguoi thuc hien (null neu he thong hoac khach chua dang nhap / login loi)
    actor_id = Column(Integer, nullable=True, index=True)
    actor_username = Column(String(100), nullable=True)
    actor_full_name = Column(String(150), nullable=True)
    actor_role = Column(Integer, nullable=True)

    # Loai hanh dong (vd: auth_login, user_role_change, secret_dispatch_download...)
    action = Column(String(60), nullable=False, index=True)

    # Doi tuong bi tac dong
    target_type = Column(String(50), nullable=True, index=True)
    target_id = Column(String(50), nullable=True)
    target_name = Column(String(255), nullable=True)

    # Thong tin an ninh mang
    ip_address = Column(String(60), nullable=True)
    is_success = Column(Boolean, nullable=False, default=True)

    # Mo ta chi tiet (chuoi text hoac JSON string)
    details = Column(Text, nullable=True)
