from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.access import allowed_classifications, can_view_classification
from app.core.roles import is_command
from app.models.directive import Directive
from app.models.user import User
from app.repositories import directive_repository, user_repository
from app.schemas.directive import (
    DirectiveAckReport,
    DirectiveAckUser,
    DirectiveCreate,
    DirectiveOut,
)

PUBLISHED = "da_ban_hanh"


def _to_out(
    directive: Directive,
    *,
    recipient_count: int,
    acknowledged_count: int,
    acknowledged_by_me: bool,
) -> DirectiveOut:
    return DirectiveOut(
        id=directive.id,
        title=directive.title,
        content=directive.content,
        status=directive.status,
        classification=directive.classification,
        author_id=directive.author_id,
        author_full_name=directive.author.full_name,
        created_at=directive.created_at,
        recipient_count=recipient_count,
        acknowledged_count=acknowledged_count,
        acknowledged_by_me=acknowledged_by_me,
    )


def _build_out(db: Session, directive: Directive, current_user: User, recipient_count: int) -> DirectiveOut:
    return _to_out(
        directive,
        recipient_count=recipient_count,
        acknowledged_count=directive_repository.count_acks(db, directive.id),
        acknowledged_by_me=directive_repository.get_ack(db, directive.id, current_user.id) is not None,
    )


def create_directive(db: Session, directive_in: DirectiveCreate, current_user: User) -> DirectiveOut:
    directive = directive_repository.create(db, directive_in, author_id=current_user.id)
    recipient_count = len(user_repository.list_active(db))
    return _build_out(db, directive, current_user, recipient_count)


def list_directives(
    db: Session, current_user: User, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None
) -> list[DirectiveOut]:
    classifications: Optional[list[str]] = None
    if not is_command(current_user):
        # Nguoi khac chi thay chi thi da ban hanh + thuoc bac ho duoc xem
        status_filter = PUBLISHED
        classifications = allowed_classifications(current_user)

    directives = directive_repository.list_all(db, skip, limit, status_filter, classifications)
    recipient_count = len(user_repository.list_active(db))
    return [_build_out(db, d, current_user, recipient_count) for d in directives]


def _get_visible_or_404(db: Session, directive_id: int, current_user: User) -> Directive:
    directive = directive_repository.get_with_author(db, directive_id)
    if directive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy chỉ thị")
    if not is_command(current_user):
        if directive.status != PUBLISHED or not can_view_classification(directive.classification, current_user):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy chỉ thị")
    return directive


def get_directive_or_404(db: Session, directive_id: int, current_user: User) -> DirectiveOut:
    directive = _get_visible_or_404(db, directive_id, current_user)
    recipient_count = len(user_repository.list_active(db))
    return _build_out(db, directive, current_user, recipient_count)


def update_directive(
    db: Session, directive_id: int, directive_in: DirectiveCreate, current_user: User
) -> DirectiveOut:
    directive = directive_repository.get_with_author(db, directive_id)
    if directive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy chỉ thị")
    updated = directive_repository.update(db, directive, directive_in)
    recipient_count = len(user_repository.list_active(db))
    return _build_out(db, updated, current_user, recipient_count)


def delete_directive(db: Session, directive_id: int, current_user: User) -> None:
    directive = directive_repository.get(db, directive_id)
    if directive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy chỉ thị")
    directive_repository.delete(db, directive)


def acknowledge_directive(db: Session, directive_id: int, current_user: User) -> DirectiveOut:
    directive = _get_visible_or_404(db, directive_id, current_user)
    if directive.status != PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chỉ thị chưa được ban hành",
        )
    if directive_repository.get_ack(db, directive_id, current_user.id) is None:
        directive_repository.add_ack(db, directive_id, current_user.id)
    recipient_count = len(user_repository.list_active(db))
    return _build_out(db, directive, current_user, recipient_count)


def get_acknowledgement_report(db: Session, directive_id: int) -> DirectiveAckReport:
    directive = directive_repository.get(db, directive_id)
    if directive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy chỉ thị")

    acks = directive_repository.list_acks(db, directive_id)
    acked_at_by_user = {a.user_id: a.acknowledged_at for a in acks}
    active_users = user_repository.list_active(db)

    acknowledged: list[DirectiveAckUser] = []
    pending: list[DirectiveAckUser] = []
    for user in active_users:
        if user.id in acked_at_by_user:
            acknowledged.append(
                DirectiveAckUser(
                    user_id=user.id,
                    full_name=user.full_name,
                    role=user.role,
                    acknowledged_at=acked_at_by_user[user.id],
                )
            )
        else:
            pending.append(
                DirectiveAckUser(user_id=user.id, full_name=user.full_name, role=user.role)
            )

    return DirectiveAckReport(
        directive_id=directive_id,
        recipient_count=len(active_users),
        acknowledged_count=len(acknowledged),
        acknowledged=acknowledged,
        pending=pending,
    )
