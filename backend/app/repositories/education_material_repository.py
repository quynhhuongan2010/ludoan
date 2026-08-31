from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.education_material import EducationMaterial
from app.schemas.education_material import EducationMaterialCreate


def create(db: Session, material_in: EducationMaterialCreate, author_id: int) -> EducationMaterial:
    material = EducationMaterial(**material_in.model_dump(), author_id=author_id)
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def list_all(
    db: Session, skip: int = 0, limit: int = 100, category: Optional[str] = None
) -> list[EducationMaterial]:
    query = db.query(EducationMaterial).options(joinedload(EducationMaterial.author))
    if category is not None:
        query = query.filter(EducationMaterial.category == category)
    return query.order_by(EducationMaterial.created_at.desc()).offset(skip).limit(limit).all()


def get_with_author(db: Session, material_id: int) -> EducationMaterial | None:
    return (
        db.query(EducationMaterial)
        .options(joinedload(EducationMaterial.author))
        .filter(EducationMaterial.id == material_id)
        .first()
    )


def get(db: Session, material_id: int) -> EducationMaterial | None:
    return db.get(EducationMaterial, material_id)


def update(db: Session, material: EducationMaterial, material_in: EducationMaterialCreate) -> EducationMaterial:
    for field, value in material_in.model_dump().items():
        setattr(material, field, value)
    db.commit()
    db.refresh(material)
    return material


def delete(db: Session, material: EducationMaterial) -> None:
    db.delete(material)
    db.commit()
