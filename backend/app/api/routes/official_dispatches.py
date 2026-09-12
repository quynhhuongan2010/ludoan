from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.uploads import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, save_secure_upload
from app.models.user import User
from app.schemas.official_dispatch import (
    AcknowledgeRequest,
    DispatchDirection,
    DispatchStatus,
    DispatchUpdate,
    DocType,
    OfficialDispatchDetailOut,
    OfficialDispatchOut,
    SecurityLevel,
    Urgency,
)
from app.services import official_dispatch_service as service

router = APIRouter(
    prefix="/official-dispatches",
    tags=["official-dispatches"],
    dependencies=[Depends(get_current_user)],
)

_ATTACH_EXT = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS


def _form_payload(
    direction: DispatchDirection = Form(...),
    doc_type: DocType = Form("cong_van"),
    dispatch_number: str = Form(..., max_length=80),
    summary: str = Form(..., max_length=500),
    issuing_org: Optional[str] = Form(None),
    receiving_org: Optional[str] = Form(None),
    signer: Optional[str] = Form(None),
    issued_date: Optional[date] = Form(None),
    received_date: Optional[date] = Form(None),
    deadline: Optional[date] = Form(None),
    page_count: Optional[int] = Form(None),
    security_level: SecurityLevel = Form("mat"),
    urgency: Urgency = Form("thuong"),
    archive_ref: Optional[str] = Form(None),
    status_value: DispatchStatus = Form("moi", alias="status"),
    note: Optional[str] = Form(None),
) -> DispatchUpdate:
    return DispatchUpdate(
        direction=direction,
        doc_type=doc_type,
        dispatch_number=dispatch_number,
        summary=summary,
        issuing_org=issuing_org,
        receiving_org=receiving_org,
        signer=signer,
        issued_date=issued_date,
        received_date=received_date,
        deadline=deadline,
        page_count=page_count,
        security_level=security_level,
        urgency=urgency,
        archive_ref=archive_ref,
        status=status_value,
        note=note,
    )


@router.get("", response_model=list[OfficialDispatchOut], status_code=status.HTTP_200_OK)
def list_dispatches(
    direction: Optional[DispatchDirection] = None,
    doc_type: Optional[DocType] = None,
    status_filter: Optional[DispatchStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_dispatches(
        db,
        current_user,
        direction=direction,
        doc_type=doc_type,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


@router.post(
    "", response_model=OfficialDispatchDetailOut, status_code=status.HTTP_201_CREATED
)
def create_dispatch(
    payload: DispatchUpdate = Depends(_form_payload),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = (
        save_secure_upload(file, subdir="dispatches", allowed_ext=_ATTACH_EXT)
        if file is not None
        else None
    )
    return service.create_dispatch(db, current_user, payload, saved)


@router.get(
    "/{dispatch_id}",
    response_model=OfficialDispatchDetailOut,
    status_code=status.HTTP_200_OK,
)
def get_dispatch(
    dispatch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_dispatch(db, current_user, dispatch_id)


@router.get("/{dispatch_id}/download")
def download_dispatch(
    dispatch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path, filename, content_type = service.get_download_target(db, current_user, dispatch_id)
    return FileResponse(path, filename=filename, media_type=content_type)


@router.put(
    "/{dispatch_id}",
    response_model=OfficialDispatchDetailOut,
    status_code=status.HTTP_200_OK,
)
def update_dispatch(
    dispatch_id: int,
    payload: DispatchUpdate = Depends(_form_payload),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = (
        save_secure_upload(file, subdir="dispatches", allowed_ext=_ATTACH_EXT)
        if file is not None
        else None
    )
    return service.update_dispatch(db, current_user, dispatch_id, payload, saved)


@router.delete("/{dispatch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dispatch(
    dispatch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_dispatch(db, current_user, dispatch_id)
    return None


@router.post(
    "/{dispatch_id}/acknowledge",
    response_model=OfficialDispatchDetailOut,
    status_code=status.HTTP_200_OK,
)
def acknowledge_dispatch(
    dispatch_id: int,
    payload: AcknowledgeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.acknowledge(db, current_user, dispatch_id, payload.response_note)
