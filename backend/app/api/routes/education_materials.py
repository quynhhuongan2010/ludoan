from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.education_material import EducationMaterialCreate, EducationMaterialOut
from app.services import education_material_service

router = APIRouter(
    prefix="/education-materials",
    tags=["education-materials"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=EducationMaterialOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def create_material(
    material_in: EducationMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return education_material_service.create_material(db, material_in, current_user)


@router.get("", response_model=list[EducationMaterialOut], status_code=status.HTTP_200_OK)
def list_materials(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return education_material_service.list_materials(db, skip, limit, category)


@router.get("/{material_id}", response_model=EducationMaterialOut, status_code=status.HTTP_200_OK)
def get_material(material_id: int, db: Session = Depends(get_db)):
    return education_material_service.get_material_or_404(db, material_id)


@router.put(
    "/{material_id}",
    response_model=EducationMaterialOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def update_material(
    material_id: int,
    material_in: EducationMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return education_material_service.update_material(db, material_id, material_in, current_user)


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("officer", "commander"))],
)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    education_material_service.delete_material(db, material_id, current_user)
    return None
