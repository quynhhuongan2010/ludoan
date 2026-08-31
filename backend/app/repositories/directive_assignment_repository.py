from datetime import date
from typing import Iterable, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.directive_assignment import (
    DirectiveAssignment,
    DirectiveAssignmentTarget,
    DirectiveSubmission,
)

_ASSIGNMENT_LOADS = (
    joinedload(DirectiveAssignment.created_by),
    joinedload(DirectiveAssignment.directive),
    joinedload(DirectiveAssignment.targets).joinedload(DirectiveAssignmentTarget.unit),
    joinedload(DirectiveAssignment.targets).joinedload(DirectiveAssignmentTarget.assignee),
    joinedload(DirectiveAssignment.targets)
    .joinedload(DirectiveAssignmentTarget.submissions)
    .joinedload(DirectiveSubmission.submitted_by),
)


def create_assignment(
    db: Session,
    *,
    directive_id: Optional[int],
    title: str,
    description: Optional[str],
    due_date: Optional[date],
    created_by_id: int,
) -> DirectiveAssignment:
    obj = DirectiveAssignment(
        directive_id=directive_id,
        title=title,
        description=description,
        due_date=due_date,
        created_by_id=created_by_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def add_targets(
    db: Session, assignment_id: int, pairs: Iterable[tuple[int, Optional[int]]]
) -> list[DirectiveAssignmentTarget]:
    created: list[DirectiveAssignmentTarget] = []
    for unit_id, assignee_id in pairs:
        t = DirectiveAssignmentTarget(
            assignment_id=assignment_id, unit_id=unit_id, assignee_id=assignee_id
        )
        db.add(t)
        created.append(t)
    db.commit()
    for t in created:
        db.refresh(t)
    return created


def get_assignment(db: Session, assignment_id: int) -> DirectiveAssignment | None:
    return (
        db.query(DirectiveAssignment)
        .options(*_ASSIGNMENT_LOADS)
        .filter(DirectiveAssignment.id == assignment_id)
        .first()
    )


def list_assignments(
    db: Session,
    *,
    see_all: bool,
    unit_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    directive_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[DirectiveAssignment]:
    query = db.query(DirectiveAssignment).options(*_ASSIGNMENT_LOADS)
    if not see_all:
        conds = []
        if unit_id is not None:
            conds.append(DirectiveAssignmentTarget.unit_id == unit_id)
        if assignee_id is not None:
            conds.append(DirectiveAssignmentTarget.assignee_id == assignee_id)
        query = query.join(
            DirectiveAssignmentTarget,
            DirectiveAssignmentTarget.assignment_id == DirectiveAssignment.id,
        ).filter(or_(*conds) if conds else False)
    if status is not None:
        query = query.filter(DirectiveAssignment.status == status)
    if directive_id is not None:
        query = query.filter(DirectiveAssignment.directive_id == directive_id)
    return (
        query.order_by(DirectiveAssignment.created_at.desc(), DirectiveAssignment.id.desc())
        .distinct()
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_assignment(
    db: Session,
    assignment: DirectiveAssignment,
    *,
    title: str,
    description: Optional[str],
    due_date: Optional[date],
    directive_id: Optional[int],
) -> DirectiveAssignment:
    assignment.title = title
    assignment.description = description
    assignment.due_date = due_date
    assignment.directive_id = directive_id
    db.commit()
    db.refresh(assignment)
    return assignment


def set_assignment_status(db: Session, assignment: DirectiveAssignment, status: str) -> None:
    if assignment.status != status:
        assignment.status = status
        db.commit()


def delete_assignment(db: Session, assignment: DirectiveAssignment) -> None:
    db.delete(assignment)
    db.commit()


def get_target(db: Session, target_id: int) -> DirectiveAssignmentTarget | None:
    return (
        db.query(DirectiveAssignmentTarget)
        .options(
            joinedload(DirectiveAssignmentTarget.unit),
            joinedload(DirectiveAssignmentTarget.assignee),
            joinedload(DirectiveAssignmentTarget.submissions).joinedload(
                DirectiveSubmission.submitted_by
            ),
        )
        .filter(DirectiveAssignmentTarget.id == target_id)
        .first()
    )


def delete_target(db: Session, target: DirectiveAssignmentTarget) -> None:
    db.delete(target)
    db.commit()


def add_submission(
    db: Session,
    *,
    target_id: int,
    content: str,
    attachment_url: Optional[str],
    submitted_by_id: int,
) -> DirectiveSubmission:
    sub = DirectiveSubmission(
        target_id=target_id,
        content=content,
        attachment_url=attachment_url,
        submitted_by_id=submitted_by_id,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def get_submission(db: Session, submission_id: int) -> DirectiveSubmission | None:
    return db.get(DirectiveSubmission, submission_id)


def latest_submission(db: Session, target_id: int) -> DirectiveSubmission | None:
    return (
        db.query(DirectiveSubmission)
        .filter(DirectiveSubmission.target_id == target_id)
        .order_by(DirectiveSubmission.created_at.desc(), DirectiveSubmission.id.desc())
        .first()
    )


def save(db: Session, obj) -> None:
    db.add(obj)
    db.commit()
    db.refresh(obj)
