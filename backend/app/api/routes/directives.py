from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.roles import COMMAND_ROLES
from app.models.user import User
from app.schemas.directive import DirectiveAckReport, DirectiveCreate, DirectiveOut
from app.services import directive_service

router = APIRouter(
    prefix="/directives",
    tags=["directives"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=DirectiveOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def create_directive(
    directive_in: DirectiveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return directive_service.create_directive(db, directive_in, current_user)


@router.get("", response_model=list[DirectiveOut], status_code=status.HTTP_200_OK)
def list_directives(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return directive_service.list_directives(db, current_user, skip, limit, status_filter)


@router.get("/{directive_id}", response_model=DirectiveOut, status_code=status.HTTP_200_OK)
def get_directive(
    directive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return directive_service.get_directive_or_404(db, directive_id, current_user)


@router.put(
    "/{directive_id}",
    response_model=DirectiveOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def update_directive(
    directive_id: int,
    directive_in: DirectiveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return directive_service.update_directive(db, directive_id, directive_in, current_user)


@router.delete(
    "/{directive_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def delete_directive(
    directive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    directive_service.delete_directive(db, directive_id, current_user)
    return None


@router.post(
    "/{directive_id}/acknowledge",
    response_model=DirectiveOut,
    status_code=status.HTTP_200_OK,
)
def acknowledge_directive(
    directive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return directive_service.acknowledge_directive(db, directive_id, current_user)


@router.get(
    "/{directive_id}/acknowledgements",
    response_model=DirectiveAckReport,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*COMMAND_ROLES))],
)
def get_acknowledgement_report(
    directive_id: int,
    db: Session = Depends(get_db),
):
    return directive_service.get_acknowledgement_report(db, directive_id)
