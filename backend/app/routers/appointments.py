# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Appointment, Pet, Service
from ..schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
from ..services.collision_service import check_groomer_collision
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

@router.get("", response_model=List[AppointmentOut])
def get_appointments(
    date: Optional[str] = Query(None, description="Lọc theo ngày (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Lọc trạng thái: CONFIRMED, COMPLETED, CANCELLED"),
    groomer: Optional[str] = Query(None, description="Lọc theo thợ Groomer"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Appointment)
    if date:
        query = query.filter(Appointment.appointment_date == date)
    if status:
        query = query.filter(Appointment.status == status.upper())
    if groomer:
        query = query.filter(Appointment.groomer_name.ilike(f"%{groomer}%"))
    return query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.asc()).all()

@router.post("/check-collision")
def check_collision(
    groomer_name: str,
    appointment_date: str,
    start_time: str,
    end_time: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    is_collided = check_groomer_collision(db, groomer_name, appointment_date, start_time, end_time)
    return {
        "is_collided": is_collided,
        "message": f"Thợ {groomer_name} ĐÃ BẬN trong khung giờ này!" if is_collided else f"Thợ {groomer_name} TRỐNG LỊCH, sẵn sàng tiếp nhận!"
    }

@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    app_in: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST"]))
):
    # Check Pet and Service existence
    pet = db.query(Pet).filter(Pet.pet_id == app_in.pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Thú cưng không tồn tại")
    srv = db.query(Service).filter(Service.service_id == app_in.service_id).first()
    if not srv:
        raise HTTPException(status_code=404, detail="Dịch vụ không tồn tại")

    # Anti-Collision Validation
    if check_groomer_collision(db, app_in.groomer_name, app_in.appointment_date, app_in.start_time, app_in.end_time):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"XUNG ĐỘT LỊCH HẸN: Thợ {app_in.groomer_name} đã có lịch bận trong khung giờ {app_in.start_time} - {app_in.end_time} ngày {app_in.appointment_date}!"
        )

    appointment = Appointment(**app_in.dict(), status="CONFIRMED")
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.put("/{app_id}", response_model=AppointmentOut)
def update_appointment(
    app_id: int,
    app_in: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST"]))
):
    app = db.query(Appointment).filter(Appointment.appointment_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")

    # If rescheduling time, check collision
    new_groomer = app_in.groomer_name or app.groomer_name
    new_date = app_in.appointment_date or app.appointment_date
    new_start = app_in.start_time or app.start_time
    new_end = app_in.end_time or app.end_time

    if new_end <= new_start:
        raise HTTPException(status_code=422, detail="Giờ kết thúc phải sau giờ bắt đầu")

    if (app_in.start_time or app_in.end_time or app_in.appointment_date or app_in.groomer_name) and (app_in.status != "CANCELLED"):
        if check_groomer_collision(db, new_groomer, new_date, new_start, new_end, exclude_id=app_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Xung đột lịch: Thợ {new_groomer} đã có lịch trong khung giờ này!"
            )

    for field, val in app_in.dict(exclude_unset=True).items():
        setattr(app, field, val)
    db.commit()
    db.refresh(app)
    return app

@router.delete("/{app_id}")
def cancel_appointment(
    app_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST"]))
):
    app = db.query(Appointment).filter(Appointment.appointment_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")
    app.status = "CANCELLED"
    db.commit()
    return {"message": "Đã hủy lịch hẹn thành công"}


@router.patch("/{app_id}/complete", response_model=AppointmentOut)
def complete_appointment(
    app_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST", "GROOMER"]))
):
    """Chỉ hoàn tất lịch đang chờ; không thay đổi lịch đã hủy hoặc hoàn tất."""
    updated = (db.query(Appointment)
               .filter(Appointment.appointment_id == app_id, Appointment.status == "CONFIRMED")
               .update({Appointment.status: "COMPLETED"}, synchronize_session=False))
    if not updated:
        existing = db.query(Appointment).filter(Appointment.appointment_id == app_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")
        raise HTTPException(status_code=409, detail="Chỉ có thể hoàn tất lịch đang chờ phục vụ")
    db.commit()
    return db.query(Appointment).filter(Appointment.appointment_id == app_id).one()
