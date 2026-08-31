from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.uploads import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, save_upload
from app.models.user import User
from app.schemas.command_meeting import (
    AttendanceUpdate,
    AttendeeOut,
    CommandMeetingCreate,
    CommandMeetingDetailOut,
    CommandMeetingOut,
    CommandMeetingUpdate,
    InviteRequest,
    MeetingStatus,
    MinutesRequest,
)
from app.services import command_meeting_service as service

router = APIRouter(
    prefix="/command-meetings",
    tags=["command-meetings"],
    dependencies=[Depends(get_current_user)],
)

_ATTACH_EXT = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS


@router.get("", response_model=list[CommandMeetingOut], status_code=status.HTTP_200_OK)
def list_meetings(
    status_filter: Optional[MeetingStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_meetings(
        db,
        current_user,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )


@router.post(
    "", response_model=CommandMeetingDetailOut, status_code=status.HTTP_201_CREATED
)
def create_meeting(
    payload: CommandMeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_meeting(db, current_user, payload)


@router.get(
    "/{meeting_id}",
    response_model=CommandMeetingDetailOut,
    status_code=status.HTTP_200_OK,
)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_meeting(db, current_user, meeting_id)


@router.put(
    "/{meeting_id}",
    response_model=CommandMeetingDetailOut,
    status_code=status.HTTP_200_OK,
)
def update_meeting(
    meeting_id: int,
    payload: CommandMeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_meeting(db, current_user, meeting_id, payload)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_meeting(db, current_user, meeting_id)
    return None


@router.post(
    "/{meeting_id}/minutes",
    response_model=CommandMeetingDetailOut,
    status_code=status.HTTP_200_OK,
)
def set_minutes(
    meeting_id: int,
    payload: MinutesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.set_minutes(
        db, current_user, meeting_id, payload.minutes, payload.mark_finished
    )


@router.post(
    "/{meeting_id}/attachment",
    response_model=CommandMeetingDetailOut,
    status_code=status.HTTP_200_OK,
)
def upload_attachment(
    meeting_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = save_upload(file, subdir="command", allowed_ext=_ATTACH_EXT)
    return service.set_attachment(db, current_user, meeting_id, saved)


@router.get("/{meeting_id}/download")
def download_attachment(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path, filename, content_type = service.get_download_target(db, current_user, meeting_id)
    return FileResponse(path, filename=filename, media_type=content_type)


@router.post(
    "/{meeting_id}/attendees",
    response_model=CommandMeetingDetailOut,
    status_code=status.HTTP_201_CREATED,
)
def invite_attendees(
    meeting_id: int,
    payload: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.invite(db, current_user, meeting_id, payload.user_ids)


@router.delete(
    "/{meeting_id}/attendees/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_attendee(
    meeting_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.remove_attendee(db, current_user, meeting_id, user_id)
    return None


@router.patch(
    "/{meeting_id}/attendees/{user_id}",
    response_model=AttendeeOut,
    status_code=status.HTTP_200_OK,
)
def update_attendance(
    meeting_id: int,
    user_id: int,
    payload: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_attendance(db, current_user, meeting_id, user_id, payload)
