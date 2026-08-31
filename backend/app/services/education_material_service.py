from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.education_material import EducationMaterial
from app.models.user import User
from app.repositories import education_material_repository
from app.schemas.education_material import EducationMaterialCreate, EducationMaterialOut


def _to_out(material: EducationMaterial) -> EducationMaterialOut:
    return EducationMaterialOut(
        id=material.id,
        title=material.title,
        category=material.category,
        period_label=material.period_label,
        content=material.content,
        attachment_url=material.attachment_url,
        author_id=material.author_id,
        author_full_name=material.author.full_name,
        created_at=material.created_at,
    )


def create_material(db: Session, material_in: EducationMaterialCreate, current_user: User) -> EducationMaterialOut:
    material = education_material_repository.create(db, material_in, author_id=current_user.id)
    return _to_out(material)


def list_materials(
    db: Session, skip: int = 0, limit: int = 100, category: Optional[str] = None
) -> list[EducationMaterialOut]:
    materials = education_material_repository.list_all(db, skip, limit, category)
    return [_to_out(m) for m in materials]


def get_material_or_404(db: Session, material_id: int) -> EducationMaterialOut:
    material = education_material_repository.get_with_author(db, material_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education material not found")
    return _to_out(material)


def _get_owned_or_404(db: Session, material_id: int, current_user: User) -> EducationMaterial:
    material = education_material_repository.get(db, material_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education material not found")
    if current_user.role != "commander" and material.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return material


def update_material(
    db: Session, material_id: int, material_in: EducationMaterialCreate, current_user: User
) -> EducationMaterialOut:
    material = _get_owned_or_404(db, material_id, current_user)
    updated = education_material_repository.update(db, material, material_in)
    return _to_out(updated)


def delete_material(db: Session, material_id: int, current_user: User) -> None:
    material = _get_owned_or_404(db, material_id, current_user)
    education_material_repository.delete(db, material)
