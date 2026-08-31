from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.item import ItemCreate, ItemOut
from app.services import item_service

router = APIRouter(prefix="/items", tags=["items"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
    return item_service.create_item(db, item_in)


@router.get("", response_model=list[ItemOut], status_code=status.HTTP_200_OK)
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return item_service.list_items(db, skip, limit)


@router.get("/{item_id}", response_model=ItemOut, status_code=status.HTTP_200_OK)
def get_item(item_id: int, db: Session = Depends(get_db)):
    return item_service.get_item_or_404(db, item_id)


@router.put("/{item_id}", response_model=ItemOut, status_code=status.HTTP_200_OK)
def update_item(item_id: int, item_in: ItemCreate, db: Session = Depends(get_db)):
    return item_service.update_item(db, item_id, item_in)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item_service.delete_item(db, item_id)
    return None
