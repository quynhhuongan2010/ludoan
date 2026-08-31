from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

UnitKind = Literal[
    "phong_ban",
    "tieu_doan",
    "dai_doi",
    "tram",
    "bch_lu_doan",
    "cap_uy",
]


class UnitCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    unit_kind: UnitKind = "phong_ban"
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True


class UnitOut(BaseModel):
    id: int
    name: str
    unit_kind: UnitKind
    description: Optional[str]
    is_active: bool
    created_at: datetime
    user_count: int

    model_config = ConfigDict(from_attributes=True)
