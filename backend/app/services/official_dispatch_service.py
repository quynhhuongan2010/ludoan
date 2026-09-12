from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.access import can_access_command_channel, is_command_level
from app.core.config import settings
from app.core.roles import COMMAND_ROLES
from app.core.uploads import SavedFile, delete_secure_upload
from app.models.official_dispatch import OfficialDispatch
from app.models.user import User
from app.repositories import official_dispatch_repository as repo
from app.services import audit_log_service
from app.schemas.official_dispatch import (
    DispatchAckOut,
    DispatchUpdate,
    OfficialDispatchDetailOut,
    OfficialDispatchOut,
)

_NOT_FOUND = "Không tìm thấy công văn"
_FORBIDDEN = "Bạn không có quyền truy cập Sổ công văn mật (yêu cầu quyền MẬT)"
_DUP = "Số hiệu công văn đã tồn tại trong sổ (theo chiều đi/đến)"


def _require_channel(user: User) -> None:
    if not can_access_command_channel(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_FORBIDDEN)


def _require_commander(user: User) -> None:
    if not is_command_level(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Ban chỉ huy được vào sổ / sửa / xoá công văn",
        )


def _recipients(db: Session) -> list[User]:
    return (
        db.query(User)
        .filter(
            User.is_active.is_(True),
            or_(User.role.in_(COMMAND_ROLES), User.clearance.is_(True)),
        )
        .order_by(User.full_name.asc())
        .all()
    )


def _to_out(db: Session, d: OfficialDispatch, current_user: User) -> OfficialDispatchOut:
    return OfficialDispatchOut(
        id=d.id,
        direction=d.direction,
        doc_type=d.doc_type,
        dispatch_number=d.dispatch_number,
        summary=d.summary,
        issuing_org=d.issuing_org,
        receiving_org=d.receiving_org,
        signer=d.signer,
        issued_date=d.issued_date,
        received_date=d.received_date,
        deadline=d.deadline,
        page_count=d.page_count,
        security_level=d.security_level,
        urgency=d.urgency,
        archive_ref=d.archive_ref,
        status=d.status,
        classification=d.classification,
        note=d.note,
        attachment_url=d.attachment_url,
        attachment_name=d.attachment_name,
        created_by_id=d.created_by_id,
        created_by_full_name=d.created_by.full_name if d.created_by else "",
        created_at=d.created_at,
        recipient_count=len(_recipients(db)),
        acknowledged_count=repo.count_acks(db, d.id),
        acknowledged_by_me=repo.get_ack(db, d.id, current_user.id) is not None,
    )


def _to_detail(db: Session, d: OfficialDispatch, current_user: User) -> OfficialDispatchDetailOut:
    base = _to_out(db, d, current_user)
    acks = {a.user_id: a for a in repo.list_acks(db, d.id)}
    acknowledged: list[DispatchAckOut] = []
    pending: list[DispatchAckOut] = []
    for u in _recipients(db):
        a = acks.get(u.id)
        if a is not None:
            acknowledged.append(
                DispatchAckOut(
                    user_id=u.id,
                    full_name=u.full_name,
                    role=u.role,
                    acknowledged_at=a.acknowledged_at,
                    response_note=a.response_note,
                )
            )
        else:
            pending.append(DispatchAckOut(user_id=u.id, full_name=u.full_name, role=u.role))
    return OfficialDispatchDetailOut(
        **base.model_dump(), acknowledged=acknowledged, pending=pending
    )


def _get_or_404(db: Session, dispatch_id: int) -> OfficialDispatch:
    d = repo.get(db, dispatch_id)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return d


def create_dispatch(
    db: Session, current_user: User, payload: DispatchUpdate, saved: Optional[SavedFile]
) -> OfficialDispatchDetailOut:
    _require_commander(current_user)
    if repo.get_by_number(db, payload.direction, payload.dispatch_number) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_DUP)
    d = repo.create(
        db,
        direction=payload.direction,
        doc_type=payload.doc_type,
        dispatch_number=payload.dispatch_number,
        summary=payload.summary,
        issuing_org=payload.issuing_org,
        receiving_org=payload.receiving_org,
        signer=payload.signer,
        issued_date=payload.issued_date,
        received_date=payload.received_date,
        deadline=payload.deadline,
        page_count=payload.page_count,
        security_level=payload.security_level,
        urgency=payload.urgency,
        archive_ref=payload.archive_ref,
        status=payload.status,
        note=payload.note,
        attachment_url=saved.url if saved else None,
        attachment_name=saved.original_name if saved else None,
        content_type=saved.content_type if saved else None,
        created_by_id=current_user.id,
    )
    return _to_detail(db, repo.get(db, d.id), current_user)


def list_dispatches(
    db: Session,
    current_user: User,
    *,
    direction: Optional[str] = None,
    doc_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[OfficialDispatchOut]:
    _require_channel(current_user)
    rows = repo.list_all(
        db,
        direction=direction,
        doc_type=doc_type,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return [_to_out(db, d, current_user) for d in rows]


def get_dispatch(
    db: Session, current_user: User, dispatch_id: int
) -> OfficialDispatchDetailOut:
    _require_channel(current_user)
    return _to_detail(db, _get_or_404(db, dispatch_id), current_user)


def update_dispatch(
    db: Session,
    current_user: User,
    dispatch_id: int,
    payload: DispatchUpdate,
    saved: Optional[SavedFile],
) -> OfficialDispatchDetailOut:
    _require_commander(current_user)
    d = _get_or_404(db, dispatch_id)
    other = repo.get_by_number(db, payload.direction, payload.dispatch_number)
    if other is not None and other.id != d.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_DUP)
    d.direction = payload.direction
    d.doc_type = payload.doc_type
    d.dispatch_number = payload.dispatch_number
    d.summary = payload.summary
    d.issuing_org = payload.issuing_org
    d.receiving_org = payload.receiving_org
    d.signer = payload.signer
    d.issued_date = payload.issued_date
    d.received_date = payload.received_date
    d.deadline = payload.deadline
    d.page_count = payload.page_count
    d.security_level = payload.security_level
    d.urgency = payload.urgency
    d.archive_ref = payload.archive_ref
    d.status = payload.status
    d.note = payload.note
    if saved is not None:
        old = d.attachment_url
        d.attachment_url = saved.url
        d.attachment_name = saved.original_name
        d.content_type = saved.content_type
        repo.save(db, d)
        delete_secure_upload(old)
    else:
        repo.save(db, d)
    return _to_detail(db, repo.get(db, d.id), current_user)


def delete_dispatch(db: Session, current_user: User, dispatch_id: int) -> None:
    _require_commander(current_user)
    d = _get_or_404(db, dispatch_id)
    attachment = d.attachment_url
    repo.delete(db, d)
    delete_secure_upload(attachment)


def acknowledge(
    db: Session, current_user: User, dispatch_id: int, response_note: Optional[str]
) -> OfficialDispatchDetailOut:
    _require_channel(current_user)
    d = _get_or_404(db, dispatch_id)
    repo.upsert_ack(db, d.id, current_user.id, response_note)
    return _to_detail(db, repo.get(db, d.id), current_user)


def get_download_target(
    db: Session, current_user: User, dispatch_id: int
) -> tuple[Path, str, str]:
    _require_channel(current_user)
    d = _get_or_404(db, dispatch_id)
    if not d.attachment_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Công văn không có tệp đính kèm"
        )
    # 1. Kiem tra trong secure_upload_path truoc (/secure/dispatches/...)
    if d.attachment_url.startswith("/secure/"):
        rel = d.attachment_url[len("/secure/") :]
        path = (settings.secure_upload_path / rel).resolve()
        if settings.secure_upload_path.resolve() in path.parents and path.is_file():
            audit_log_service.record_action(
                db,
                action="secret_dispatch_download",
                actor=current_user,
                target_type="official_dispatch",
                target_id=str(d.id),
                target_name=f"[{d.dispatch_number}] {d.summary}",
                is_success=True,
                details=f"Tải tệp đính kèm: {d.attachment_name or path.name}",
            )
            return path, d.attachment_name or path.name, d.content_type or "application/octet-stream"

    # 2. Fallback tuong thich nguoc cho file cu trong upload_path (/static/command/...)
    rel = (
        d.attachment_url[len("/static/") :]
        if d.attachment_url.startswith("/static/")
        else d.attachment_url
    )
    path = (settings.upload_path / rel).resolve()
    if settings.upload_path.resolve() in path.parents and path.is_file():
        audit_log_service.record_action(
            db,
            action="secret_dispatch_download",
            actor=current_user,
            target_type="official_dispatch",
            target_id=str(d.id),
            target_name=f"[{d.dispatch_number}] {d.summary}",
            is_success=True,
            details=f"Tải tệp đính kèm (bản cũ): {d.attachment_name or path.name}",
        )
        return path, d.attachment_name or path.name, d.content_type or "application/octet-stream"

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="File không tồn tại trên máy chủ"
    )
