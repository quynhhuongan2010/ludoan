from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.contacts_import import map_standard_fields, parse_contacts_file
from app.models.contact import Contact, ContactBook
from app.models.user import User
from app.repositories import contact_repository as repo
from app.schemas.contact import ContactBookOut, ContactOut, ContactPage

_NOT_FOUND = "Không tìm thấy bộ danh bạ"


def _cut(v: Optional[str], n: int) -> Optional[str]:
    if not v:
        return None
    v = v.strip()
    return v[:n] if v else None


def _book_out(b: ContactBook) -> ContactBookOut:
    return ContactBookOut(
        id=b.id,
        name=b.name,
        description=b.description,
        source_file_name=b.source_file_name,
        column_headers=b.column_headers or [],
        row_count=b.row_count,
        created_by_id=b.created_by_id,
        created_by_full_name=b.created_by.full_name if b.created_by else "",
        created_at=b.created_at,
    )


def _contact_out(c: Contact) -> ContactOut:
    return ContactOut(
        id=c.id,
        book_id=c.book_id,
        row_index=c.row_index,
        full_name=c.full_name,
        unit=c.unit,
        position=c.position,
        phone=c.phone,
        email=c.email,
        extra=c.extra or {},
    )


def _get_book_or_404(db: Session, book_id: int) -> ContactBook:
    b = repo.get_book(db, book_id)
    if b is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return b


def list_books(db: Session) -> list[ContactBookOut]:
    return [_book_out(b) for b in repo.list_books(db)]


def get_book(db: Session, book_id: int) -> ContactBookOut:
    return _book_out(_get_book_or_404(db, book_id))


def import_book(
    db: Session,
    current_user: User,
    *,
    name: str,
    description: str,
    filename: str,
    data: bytes,
) -> ContactBookOut:
    headers, rows = parse_contacts_file(filename, data)

    book_name = (name or "").strip() or (filename or "Danh bạ").rsplit(".", 1)[0].strip() or "Danh bạ"
    book = repo.create_book(
        db,
        name=book_name[:255],
        description=(description.strip() or None) if description else None,
        source_file_name=(filename or None),
        column_headers=headers,
        created_by_id=current_user.id,
    )

    payload: list[dict] = []
    for i, row in enumerate(rows):
        std = map_standard_fields(row)
        blob = " ".join(str(v) for v in row.values() if v).lower()[:60000]
        payload.append(
            dict(
                row_index=i,
                full_name=_cut(std["full_name"], 255),
                unit=_cut(std["unit"], 255),
                position=_cut(std["position"], 255),
                phone=_cut(std["phone"], 100),
                email=_cut(std["email"], 255),
                extra=row,
                search_blob=blob,
            )
        )
    n = repo.bulk_add_contacts(db, book.id, payload)
    repo.finalize_book(db, book, n)
    return _book_out(repo.get_book(db, book.id))


def delete_book(db: Session, current_user: User, book_id: int) -> None:
    repo.delete_book(db, _get_book_or_404(db, book_id))


def list_contacts(
    db: Session, book_id: int, *, q: Optional[str], skip: int, limit: int
) -> ContactPage:
    b = _get_book_or_404(db, book_id)
    items, total = repo.list_contacts(db, book_id, q=q, skip=skip, limit=limit)
    return ContactPage(
        items=[_contact_out(c) for c in items],
        total=total,
        skip=skip,
        limit=limit,
        columns=b.column_headers or [],
    )
