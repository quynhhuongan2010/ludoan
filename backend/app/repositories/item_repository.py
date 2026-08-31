from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate


def create(db: Session, item_in: ItemCreate) -> Item:
    item = Item(**item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_all(db: Session, skip: int = 0, limit: int = 100) -> list[Item]:
    return db.query(Item).offset(skip).limit(limit).all()


def get(db: Session, item_id: int) -> Item | None:
    return db.get(Item, item_id)


def update(db: Session, item: Item, item_in: ItemCreate) -> Item:
    for field, value in item_in.model_dump().items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete(db: Session, item: Item) -> None:
    db.delete(item)
    db.commit()
