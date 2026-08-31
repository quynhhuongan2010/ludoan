from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.item import Item
from app.repositories import item_repository
from app.schemas.item import ItemCreate


def create_item(db: Session, item_in: ItemCreate) -> Item:
    return item_repository.create(db, item_in)


def list_items(db: Session, skip: int = 0, limit: int = 100) -> list[Item]:
    return item_repository.list_all(db, skip, limit)


def get_item_or_404(db: Session, item_id: int) -> Item:
    item = item_repository.get(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


def update_item(db: Session, item_id: int, item_in: ItemCreate) -> Item:
    item = get_item_or_404(db, item_id)
    return item_repository.update(db, item, item_in)


def delete_item(db: Session, item_id: int) -> None:
    item = get_item_or_404(db, item_id)
    item_repository.delete(db, item)
