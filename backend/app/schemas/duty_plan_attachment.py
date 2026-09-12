from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# Cho phep moi loai file lich truc thuong dung: tai lieu van phong + anh scan.
MAX_LABEL_LEN = 200


class DutyPlanAttachmentCreate(BaseModel):
    """Chi phan metadata - tep gui qua multipart `file`. Route dung `Form`/`File`,
    schema nay de mo ta hop dong & tai su dung kiem tra do dai `label`."""

    label: Optional[str] = Field(None, max_length=MAX_LABEL_LEN)


class DutyPlanAttachmentOut(BaseModel):
    id: int
    week_plan_id: int
    file_url: str
    original_name: str
    file_size: int
    content_type: Optional[str]
    label: Optional[str]
    uploaded_by_id: int
    uploaded_by_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
