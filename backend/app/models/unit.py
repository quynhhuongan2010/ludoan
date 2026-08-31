from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.core.database import Base


class Unit(Base):
    """Don vi trong to chuc Lu doan (phong ban, tieu doan, dai doi, tram, BCH, cap uy).

    Admin quan ly duoc (them/sua/xoa). Moi User co the gan `unit_id` tro toi day.
    """

    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(120), unique=True, nullable=False, index=True)
    # phong_ban | tieu_doan | dai_doi | tram | bch_lu_doan | cap_uy
    unit_kind = Column(String(30), nullable=False, server_default="phong_ban", index=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="1")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
