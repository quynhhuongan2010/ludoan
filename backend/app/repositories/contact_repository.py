from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.contact import Contact, ContactBook


def create_book(
    db: Session,
    *,
    name: str,
    description: Optional[str],
    source_file_name: Optional[str],
    column_headers: list[str],
    created_by_id: int,
) -> ContactBook:
    book = ContactBook(
        name=name,
        description=description,
        source_file_name=source_file_name,
        column_headers=column_headers,
        row_count=0,
        created_by_id=created_by_id,
    )
    db.add(book)
    db.flush()  # can book.id
    return book


def bulk_add_contacts(db: Session, book_id: int, contacts: list[dict]) -> int:
    db.bulk_save_objects([Contact(book_id=book_id, **c) for c in contacts])
    return len(contacts)


def finalize_book(db: Session, book: ContactBook, row_count: int) -> ContactBook:
    book.row_count = row_count
    db.commit()
    db.refresh(book)
    return book


def list_books(db: Session) -> list[ContactBook]:
    return (
        db.query(ContactBook)
        .options(joinedload(ContactBook.created_by))
        .order_by(ContactBook.created_at.desc(), ContactBook.id.desc())
        .all()
    )


def get_book(db: Session, book_id: int) -> ContactBook | None:
    return (
        db.query(ContactBook)
        .options(joinedload(ContactBook.created_by))
        .filter(ContactBook.id == book_id)
        .first()
    )


def delete_book(db: Session, book: ContactBook) -> None:
    db.delete(book)
    db.commit()


def list_contacts(
    db: Session, book_id: int, *, q: Optional[str], skip: int, limit: int
) -> tuple[list[Contact], int]:
    query = db.query(Contact).filter(Contact.book_id == book_id)
    if q and q.strip():
        needle = f"%{q.strip().lower()}%"
        query = query.filter(Contact.search_blob.like(needle))
    total = query.count()
    items = query.order_by(Contact.row_index.asc()).offset(skip).limit(limit).all()
    return items, total
