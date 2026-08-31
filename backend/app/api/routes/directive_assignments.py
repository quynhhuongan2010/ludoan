from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.uploads import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, save_upload
from app.models.user import User
from app.schemas.directive_assignment import (
    DirectiveAssignmentCreate,
    DirectiveAssignmentDetailOut,
    DirectiveAssignmentOut,
    DirectiveAssignmentUpdate,
    ReviewRequest,
    TargetCreate,
    TargetDetailOut,
)
from app.services import directive_assignment_service as service

router = APIRouter(
    prefix="/directive-assignments",
    tags=["directive-assignments"],
    dependencies=[Depends(get_current_user)],
)

_ATTACH_EXT = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS


@router.get("", response_model=list[DirectiveAssignmentOut], status_code=status.HTTP_200_OK)
def list_assignments(
    status_filter: Optional[str] = None,
    directive_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_assignments(
        db,
        current_user,
        status_filter=status_filter,
        directive_id=directive_id,
        skip=skip,
        limit=limit,
    )


@router.post(
    "", response_model=DirectiveAssignmentDetailOut, status_code=status.HTTP_201_CREATED
)
def create_assignment(
    payload: DirectiveAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_assignment(db, current_user, payload)


@router.get(
    "/{assignment_id}",
    response_model=DirectiveAssignmentDetailOut,
    status_code=status.HTTP_200_OK,
)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_assignment(db, current_user, assignment_id)


@router.put(
    "/{assignment_id}",
    response_model=DirectiveAssignmentDetailOut,
    status_code=status.HTTP_200_OK,
)
def update_assignment(
    assignment_id: int,
    payload: DirectiveAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_assignment(db, current_user, assignment_id, payload)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_assignment(db, current_user, assignment_id)
    return None


@router.post(
    "/{assignment_id}/targets",
    response_model=DirectiveAssignmentDetailOut,
    status_code=status.HTTP_201_CREATED,
)
def add_targets(
    assignment_id: int,
    targets: list[TargetCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.add_targets(db, current_user, assignment_id, targets)


@router.delete(
    "/{assignment_id}/targets/{target_id}", status_code=status.HTTP_200_OK,
    response_model=DirectiveAssignmentDetailOut,
)
def remove_target(
    assignment_id: int,
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.remove_target(db, current_user, assignment_id, target_id)


@router.post(
    "/{assignment_id}/targets/{target_id}/submit",
    response_model=TargetDetailOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_report(
    assignment_id: int,
    target_id: int,
    content: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = (
        save_upload(file, subdir="documents", allowed_ext=_ATTACH_EXT)
        if file is not None
        else None
    )
    return service.submit_report(
        db, current_user, assignment_id, target_id, content, saved
    )


@router.post(
    "/{assignment_id}/targets/{target_id}/review",
    response_model=TargetDetailOut,
    status_code=status.HTTP_200_OK,
)
def review_target(
    assignment_id: int,
    target_id: int,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.review_target(db, current_user, assignment_id, target_id, payload)
