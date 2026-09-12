from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.roles import can_post_content, is_command
from app.models.duty_schedule import DutySchedule
from app.models.duty_shift_handover import DutyShiftHandover
from app.models.user import User
from app.repositories import duty_shift_handover_repository as repo
from app.schemas.duty_shift_handover import (
    DutyShiftHandoverAcknowledge,
    DutyShiftHandoverCommanderReview,
    DutyShiftHandoverCreate,
    DutyShiftHandoverListResponse,
    DutyShiftHandoverOut,
)
from app.services import audit_log_service


def _to_out(h: DutyShiftHandover) -> DutyShiftHandoverOut:
    duty_date = h.schedule.duty_date if h.schedule else None
    duty_type = h.schedule.duty_type if h.schedule else None
    shift = h.schedule.shift if h.schedule else None
    unit_name = (
        h.schedule.unit.name if (h.schedule and h.schedule.unit) else None
    )

    return DutyShiftHandoverOut(
        id=h.id,
        schedule_id=h.schedule_id,
        duty_date=duty_date,
        duty_type=duty_type,
        shift=shift,
        unit_name=unit_name,
        giver_id=h.giver_id,
        giver_name=h.giver_name,
        receiver_id=h.receiver_id,
        receiver_name=h.receiver_name,
        handover_time=h.handover_time,
        personnel_report=h.personnel_report,
        equipment_status=h.equipment_status,
        incident_log=h.incident_log,
        pending_tasks=h.pending_tasks,
        commander_note=h.commander_note,
        status=h.status,
        receiver_note=h.receiver_note,
        acknowledged_at=h.acknowledged_at,
        created_at=h.created_at,
        updated_at=h.updated_at,
    )


def create_handover(
    db: Session, current_user: User, payload: DutyShiftHandoverCreate
) -> DutyShiftHandoverOut:
    # 0. Chi can bo truc (role 0..4) moi duoc lap bien ban ban giao; tai khoan
    #    "chi xem" (role 5) khong duoc.
    if not can_post_content(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ cán bộ trong biên chế kíp trực mới được lập biên bản bàn giao ca trực.",
        )

    # 1. Kiem tra dong ca truc co ton tai khong
    schedule = db.query(DutySchedule).filter(DutySchedule.id == payload.schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin ca trực tương ứng",
        )

    if payload.receiver_id is not None and payload.receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự bàn giao ca trực cho chính mình.",
        )

    # Kiem tra ca truc da co bien ban ban giao chua
    existing = repo.get_by_schedule_id(db, payload.schedule_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ca trực này đã được lập biên bản bàn giao trước đó",
        )

    giver_name = payload.giver_name or current_user.full_name or current_user.username
    handover = DutyShiftHandover(
        schedule_id=payload.schedule_id,
        giver_id=current_user.id,
        giver_name=giver_name,
        receiver_id=payload.receiver_id,
        receiver_name=payload.receiver_name,
        personnel_report=payload.personnel_report,
        equipment_status=payload.equipment_status,
        incident_log=payload.incident_log,
        pending_tasks=payload.pending_tasks,
        status="cho_nhan",
    )

    created = repo.create(db, handover)

    # Ghi log an ninh
    audit_log_service.record_action(
        db,
        action="DUTY_HANDOVER_CREATED",
        actor=current_user,
        target_type="duty_handover",
        target_id=str(created.id),
        target_name=f"Ca trực {schedule.shift} ({schedule.duty_date})",
        details=f"Đồng chí {giver_name} đã lập biên bản bàn giao ca trực",
    )

    # Lay lai kem eager load
    loaded = repo.get_by_id(db, created.id)
    return _to_out(loaded or created)


def acknowledge_handover(
    db: Session,
    current_user: User,
    handover_id: int,
    payload: DutyShiftHandoverAcknowledge,
) -> DutyShiftHandoverOut:
    handover = repo.get_by_id(db, handover_id)
    if not handover:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy biên bản bàn giao ca trực",
        )

    # 1. Chi ky nhan duoc khi bien ban con "cho_nhan" - khong ghi de bien ban
    #    da ky nhan / da co y kien chi huy.
    if handover.status != "cho_nhan":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Biên bản bàn giao ca trực này đã được ký nhận trước đó.",
        )

    # 2. Phan quyen ky nhan:
    #    - Ban Chi huy (role 0..3): luon duoc (ky nhan thay khi can).
    #    - Nguoi lap bien ban khong tu ky nhan cho minh.
    #    - Neu bien ban da chi dinh nguoi nhan: chi dung nguoi do.
    #    - Neu chua chi dinh: phai la can bo (role 0..4), khong nhan tai khoan role 5.
    if not is_command(current_user):
        if current_user.id == handover.giver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Người lập biên bản không thể tự ký nhận bàn giao ca trực.",
            )
        if handover.receiver_id is not None:
            if current_user.id != handover.receiver_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Biên bản bàn giao ca trực này được chỉ định cho quân nhân khác ký nhận.",
                )
        elif not can_post_content(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ cán bộ trong biên chế kíp trực mới được ký nhận bàn giao ca trực.",
            )

    receiver_name = current_user.full_name or current_user.username
    handover.receiver_id = current_user.id
    handover.receiver_name = receiver_name
    handover.status = payload.status
    handover.receiver_note = payload.receiver_note
    handover.acknowledged_at = datetime.now()

    db.commit()
    db.refresh(handover)

    # Ghi log an ninh
    audit_log_service.record_action(
        db,
        action="DUTY_HANDOVER_ACKNOWLEDGED",
        actor=current_user,
        target_type="duty_handover",
        target_id=str(handover.id),
        target_name=f"Biên bản ca {handover.id}",
        details=f"Đồng chí {receiver_name} đã ký nhận ca trực (trạng thái: {payload.status})",
    )

    return _to_out(handover)


def review_handover(
    db: Session,
    current_user: User,
    handover_id: int,
    payload: DutyShiftHandoverCommanderReview,
) -> DutyShiftHandoverOut:
    # Chi cap Chi huy (role <= 3) moi duoc phep kiem tra va ghi nhan xet
    if not is_command(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ cán bộ Chỉ huy mới có quyền kiểm tra và ghi ý kiến chỉ đạo vào sổ ca trực",
        )

    handover = repo.get_by_id(db, handover_id)
    if not handover:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy biên bản bàn giao ca trực",
        )

    inspector_name = current_user.full_name or current_user.username
    new_note = f"[{inspector_name} - {datetime.now().strftime('%H:%M %d/%m')}]: {payload.commander_note}"
    if handover.commander_note:
        handover.commander_note += f"\n{new_note}"
    else:
        handover.commander_note = new_note

    db.commit()
    db.refresh(handover)

    audit_log_service.record_action(
        db,
        action="DUTY_HANDOVER_REVIEWED",
        actor=current_user,
        target_type="duty_handover",
        target_id=str(handover.id),
        target_name=f"Biên bản ca {handover.id}",
        details=f"Chỉ huy {inspector_name} đã kiểm tra và ghi ý kiến chỉ đạo",
    )

    return _to_out(handover)


def get_by_schedule(db: Session, schedule_id: int) -> Optional[DutyShiftHandoverOut]:
    handover = repo.get_by_schedule_id(db, schedule_id)
    return _to_out(handover) if handover else None


def list_handovers(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    unit_id: Optional[int] = None,
    status: Optional[str] = None,
) -> DutyShiftHandoverListResponse:
    items = repo.list_all(
        db,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        unit_id=unit_id,
        status=status,
    )
    total = repo.count_all(
        db, date_from=date_from, date_to=date_to, unit_id=unit_id, status=status
    )

    return DutyShiftHandoverListResponse(
        items=[_to_out(i) for i in items],
        total=total,
        skip=skip,
        limit=limit,
    )
