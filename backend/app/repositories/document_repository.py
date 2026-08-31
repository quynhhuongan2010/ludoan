from typing import Optional, Sequence

from sqlalchemy.orm import Session, joinedload

from app.models.document import Document

_ORDER = Document.created_at.desc()


def create(
    db: Session,
    *,
    title: str,
    description: Optional[str],
    category: str,
    classification: str,
    file_url: str,
    file_name: str,
    file_size: int,
    content_type: str,
    uploaded_by_id: int,
) -> Document:
    doc = Document(
        title=title,
        description=description,
        category=category,
        classification=classification,
        file_url=file_url,
        file_name=file_name,
        file_size=file_size,
        content_type=content_type,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_all(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    classifications: Optional[Sequence[str]] = None,
) -> list[Document]:
    query = db.query(Document).options(joinedload(Document.uploaded_by))
    if category is not None:
        query = query.filter(Document.category == category)
    if classifications is not None:
        query = query.filter(Document.classification.in_(list(classifications)))
    return query.order_by(_ORDER).offset(skip).limit(limit).all()


def get_with_uploader(db: Session, doc_id: int) -> Document | None:
    return (
        db.query(Document)
        .options(joinedload(Document.uploaded_by))
        .filter(Document.id == doc_id)
        .first()
    )


def get(db: Session, doc_id: int) -> Document | None:
    return db.get(Document, doc_id)


def save(db: Session, doc: Document) -> Document:
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def delete(db: Session, doc: Document) -> None:
    db.delete(doc)
    db.commit()
