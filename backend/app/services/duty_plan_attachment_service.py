from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.uploads import (
    DOCUMENT_EXTENSIONS,
    IMAGE_EXTENSIONS,
    delete_upload,
    save_upload,
)
from app.models.user import User
from app.repositories import duty_plan_attachment_repository
from app.schemas.duty_plan_attachment import MAX_LABEL_LEN, DutyPlanAttachmentOut
from app.services.duty_week_plan_service import (
    _get_plan_or_404,
    _is_command_level,
    _require_owner_unit,
    _require_visible,
)

# "Tat ca cac loai file lich truc": tai lieu van phong + anh scan.
DUTY_ATTACH_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS
_SUBDIR = "duty-plans"


def _to_out(row) -> DutyPlanAttachmentOut:
    return DutyPlanAttachmentOut(
        id=row.id,
        week_plan_id=row.week_plan_id,
        file_url=row.file_url,
        original_name=row.original_name,
        file_size=row.file_size,
        content_type=row.content_type,
        label=row.label,
        uploaded_by_id=row.uploaded_by_id,
        uploaded_by_name=row.uploaded_by.full_name if row.uploaded_by is not None else "—",
        created_at=row.created_at,
    )


def list_attachments(db: Session, plan_id: int, current_user: User) -> list[DutyPlanAttachmentOut]:
    plan = _get_plan_or_404(db, plan_id)
    _require_visible(plan, current_user)
    return [_to_out(r) for r in duty_plan_attachment_repository.list_for_plan(db, plan_id)]


def add_attachment(
    db: Session,
    plan_id: int,
    file: UploadFile,
    label: str | None,
    current_user: User,
) -> DutyPlanAttachmentOut:
    plan = _get_plan_or_404(db, plan_id)
    _require_owner_unit(plan, current_user)  # truc ban dung don vi hoac chi huy
    clean_label = (label or "").strip()[:MAX_LABEL_LEN] or None
    saved = save_upload(file, _SUBDIR, DUTY_ATTACH_EXTENSIONS)
    row = duty_plan_attachment_repository.create(
        db,
        week_plan_id=plan.id,
        file_url=saved.url,
        original_name=saved.original_name,
        file_size=saved.size,
        content_type=saved.content_type,
        label=clean_label,
        uploaded_by_id=current_user.id,
    )
    return _to_out(row)


def delete_attachment(db: Session, plan_id: int, attachment_id: int, current_user: User) -> None:
    _get_plan_or_404(db, plan_id)
    row = duty_plan_attachment_repository.get(db, attachment_id)
    if row is None or row.week_plan_id != plan_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tệp đính kèm"
        )
    if not _is_command_level(current_user) and row.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người tải lên hoặc chỉ huy mới xoá được tệp đính kèm",
        )
    file_url = row.file_url
    duty_plan_attachment_repository.delete(db, row)
    delete_upload(file_url)
