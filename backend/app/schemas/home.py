from pydantic import BaseModel

from app.schemas.announcement import AnnouncementOut
from app.schemas.directive import DirectiveOut
from app.schemas.document import DocumentOut
from app.schemas.education_material import EducationMaterialOut
from app.schemas.post import PostOut


class HomeSummaryOut(BaseModel):
    """Trang chu ben trong (da dang nhap) - da loc theo quyen cua user."""

    latest_posts: list[PostOut]
    latest_education_materials: list[EducationMaterialOut]
    latest_directives: list[DirectiveOut]
    latest_announcements: list[AnnouncementOut]


class PublicHomeOut(BaseModel):
    """Trang cong khai cho khach chua dang nhap - chi noi dung cong_khai / is_public."""

    featured_posts: list[PostOut]
    public_announcements: list[AnnouncementOut]
    public_documents: list[DocumentOut]
