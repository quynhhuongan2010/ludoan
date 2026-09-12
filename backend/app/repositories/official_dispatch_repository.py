from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.official_dispatch import DispatchAcknowledgement, OfficialDispatch


def create(db: Session, **fields) -> OfficialDispatch:
    obj = OfficialDispatch(**fields)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def save(db: Session, obj: OfficialDispatch) -> OfficialDispatch:
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get(db: Session, dispatch_id: int) -> OfficialDispatch | None:
    return (
        db.query(OfficialDispatch)
        .options(joinedload(OfficialDispatch.created_by))
        .filter(OfficialDispatch.id == dispatch_id)
        .first()
    )


def get_by_number(db: Session, direction: str, number: str) -> OfficialDispatch | None:
    return (
        db.query(OfficialDispatch)
        .filter(
            OfficialDispatch.direction == direction,
            OfficialDispatch.dispatch_number == number,
        )
        .first()
    )


def list_all(
    db: Session,
    *,
    direction: Optional[str] = None,
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[OfficialDispatch]:
    query = db.query(OfficialDispatch).options(joinedload(OfficialDispatch.created_by))
    if direction is not None:
        query = query.filter(OfficialDispatch.direction == direction)
    if doc_type is not None:
        query = query.filter(OfficialDispatch.doc_type == doc_type)
    if status is not None:
        query = query.filter(OfficialDispatch.status == status)
    return (
        query.order_by(OfficialDispatch.created_at.desc(), OfficialDispatch.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete(db: Session, obj: OfficialDispatch) -> None:
    db.delete(obj)
    db.commit()


def get_ack(db: Session, dispatch_id: int, user_id: int) -> DispatchAcknowledgement | None:
    return (
        db.query(DispatchAcknowledgement)
        .filter(
            DispatchAcknowledgement.dispatch_id == dispatch_id,
            DispatchAcknowledgement.user_id == user_id,
        )
        .first()
    )


def list_acks(db: Session, dispatch_id: int) -> list[DispatchAcknowledgement]:
    return (
        db.query(DispatchAcknowledgement)
        .filter(DispatchAcknowledgement.dispatch_id == dispatch_id)
        .all()
    )


def count_acks(db: Session, dispatch_id: int) -> int:
    return (
        db.query(DispatchAcknowledgement)
        .filter(DispatchAcknowledgement.dispatch_id == dispatch_id)
        .count()
    )


def upsert_ack(
    db: Session, dispatch_id: int, user_id: int, response_note: Optional[str]
) -> DispatchAcknowledgement:
    row = get_ack(db, dispatch_id, user_id)
    if row is None:
        row = DispatchAcknowledgement(
            dispatch_id=dispatch_id, user_id=user_id, response_note=response_note
        )
        db.add(row)
    elif response_note is not None:
        row.response_note = response_note
    db.commit()
    db.refresh(row)
    return row
