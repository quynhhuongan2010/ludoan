from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.home import HomeSummaryOut, PublicHomeOut
from app.services import (
    announcement_service,
    directive_service,
    document_service,
    education_material_service,
    post_service,
)


def get_summary(db: Session, current_user: User, limit: int = 5) -> HomeSummaryOut:
    return HomeSummaryOut(
        latest_posts=post_service.list_posts(db, current_user, skip=0, limit=limit),
        latest_education_materials=education_material_service.list_materials(db, skip=0, limit=limit),
        latest_directives=directive_service.list_directives(db, current_user, skip=0, limit=limit),
        latest_announcements=announcement_service.list_announcements(db, current_user, skip=0, limit=limit),
    )


def get_public_summary(db: Session, limit: int = 6) -> PublicHomeOut:
    """Chi noi dung mo cho khach: bai cong_khai (uu tien noi bat), thong bao is_public, tai lieu cong_khai."""
    return PublicHomeOut(
        featured_posts=post_service.list_featured_public(db, limit=limit),
        public_announcements=announcement_service.list_announcements(db, None, skip=0, limit=limit),
        public_documents=document_service.list_documents(db, None, skip=0, limit=limit),
    )
