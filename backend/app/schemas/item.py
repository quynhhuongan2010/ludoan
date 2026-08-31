from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class ItemOut(ItemCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
