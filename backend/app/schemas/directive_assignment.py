from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AssignmentStatus = Literal["chua_giao", "dang_thuc_hien", "hoan_thanh", "qua_han"]
TargetStatus = Literal["chua_nop", "cho_duyet", "da_duyet", "tra_lai"]
ReviewResult = Literal["da_duyet", "tra_lai"]


class TargetCreate(BaseModel):
    unit_id: int
    assignee_id: Optional[int] = None


class DirectiveAssignmentCreate(BaseModel):
    directive_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    targets: list[TargetCreate] = Field(default_factory=list)


class DirectiveAssignmentUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    directive_id: Optional[int] = None


class ReviewRequest(BaseModel):
    result: ReviewResult
    review_note: Optional[str] = Field(default=None, max_length=500)


class SubmissionOut(BaseModel):
    id: int
    target_id: int
    content: str
    attachment_url: Optional[str]
    submitted_by_id: int
    submitted_by_full_name: str
    created_at: datetime
    review_result: Optional[ReviewResult]
    review_note: Optional[str]
    reviewed_by_id: Optional[int]
    reviewed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TargetOut(BaseModel):
    id: int
    assignment_id: int
    unit_id: int
    unit_name: str
    assignee_id: Optional[int]
    assignee_full_name: Optional[str]
    status: TargetStatus
    submitted_at: Optional[datetime]
    submission_count: int

    model_config = ConfigDict(from_attributes=True)


class TargetDetailOut(TargetOut):
    submissions: list[SubmissionOut]


class DirectiveAssignmentOut(BaseModel):
    id: int
    directive_id: Optional[int]
    directive_title: Optional[str]
    title: str
    description: Optional[str]
    due_date: Optional[date]
    status: AssignmentStatus
    created_by_id: int
    created_by_full_name: str
    created_at: datetime
    target_count: int
    approved_count: int
    pending_count: int

    model_config = ConfigDict(from_attributes=True)


class DirectiveAssignmentDetailOut(DirectiveAssignmentOut):
    targets: list[TargetDetailOut]
