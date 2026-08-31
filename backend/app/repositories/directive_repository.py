from typing import Optional, Sequence

from sqlalchemy.orm import Session, joinedload

from app.models.directive import Directive, DirectiveAcknowledgement
from app.schemas.directive import DirectiveCreate


def create(db: Session, directive_in: DirectiveCreate, author_id: int) -> Directive:
    directive = Directive(**directive_in.model_dump(), author_id=author_id)
    db.add(directive)
    db.commit()
    db.refresh(directive)
    return directive


def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    classifications: Optional[Sequence[str]] = None,
) -> list[Directive]:
    query = db.query(Directive).options(joinedload(Directive.author))
    if status is not None:
        query = query.filter(Directive.status == status)
    if classifications is not None:
        query = query.filter(Directive.classification.in_(list(classifications)))
    return query.order_by(Directive.created_at.desc()).offset(skip).limit(limit).all()


def get_with_author(db: Session, directive_id: int) -> Directive | None:
    return (
        db.query(Directive)
        .options(joinedload(Directive.author))
        .filter(Directive.id == directive_id)
        .first()
    )


def get(db: Session, directive_id: int) -> Directive | None:
    return db.get(Directive, directive_id)


def update(db: Session, directive: Directive, directive_in: DirectiveCreate) -> Directive:
    for field, value in directive_in.model_dump().items():
        setattr(directive, field, value)
    db.commit()
    db.refresh(directive)
    return directive


def delete(db: Session, directive: Directive) -> None:
    db.delete(directive)
    db.commit()


def get_ack(db: Session, directive_id: int, user_id: int) -> DirectiveAcknowledgement | None:
    return (
        db.query(DirectiveAcknowledgement)
        .filter(
            DirectiveAcknowledgement.directive_id == directive_id,
            DirectiveAcknowledgement.user_id == user_id,
        )
        .first()
    )


def add_ack(db: Session, directive_id: int, user_id: int) -> DirectiveAcknowledgement:
    ack = DirectiveAcknowledgement(directive_id=directive_id, user_id=user_id)
    db.add(ack)
    db.commit()
    db.refresh(ack)
    return ack


def list_acks(db: Session, directive_id: int) -> list[DirectiveAcknowledgement]:
    return (
        db.query(DirectiveAcknowledgement)
        .options(joinedload(DirectiveAcknowledgement.user))
        .filter(DirectiveAcknowledgement.directive_id == directive_id)
        .all()
    )


def count_acks(db: Session, directive_id: int) -> int:
    return (
        db.query(DirectiveAcknowledgement)
        .filter(DirectiveAcknowledgement.directive_id == directive_id)
        .count()
    )
