# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import CareRecord, Pet, Appointment
from ..schemas import CareRecordCreate, CareRecordOut, CareRecordUpdate
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/care-records", tags=["Care Records"])

@router.get("", response_model=List[CareRecordOut])
def get_care_records(
    pet_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(CareRecord)
    if pet_id:
        query = query.filter(CareRecord.pet_id == pet_id)
    return query.order_by(CareRecord.record_date.desc()).all()

@router.post("", response_model=CareRecordOut, status_code=status.HTTP_201_CREATED)
def create_care_record(
    rec_in: CareRecordCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "GROOMER", "RECEPTIONIST"]))
):
    pet = db.query(Pet).filter(Pet.pet_id == rec_in.pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Thú cưng không tồn tại")
    app = None
    if rec_in.appointment_id is not None:
        app = db.query(Appointment).filter(Appointment.appointment_id == rec_in.appointment_id).first()
        if not app:
            raise HTTPException(status_code=404, detail="Không tìm thấy lịch hẹn")
        if app.pet_id != rec_in.pet_id:
            raise HTTPException(status_code=422, detail="Lịch hẹn không thuộc thú cưng này")
        if app.status == "CANCELLED":
            raise HTTPException(status_code=409, detail="Không thể tạo hồ sơ cho lịch hẹn đã hủy")
    rec = CareRecord(**rec_in.model_dump())
    db.add(rec)
    if app is not None:
        app.status = "COMPLETED"
    db.commit()
    db.refresh(rec)
    return rec

def _get_record(db: Session, care_id: int) -> CareRecord:
    rec = db.query(CareRecord).filter(CareRecord.care_id == care_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ chăm sóc")
    return rec

@router.get("/{care_id}", response_model=CareRecordOut)
def get_care_record(care_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return _get_record(db, care_id)

@router.put("/{care_id}", response_model=CareRecordOut)
def update_care_record(
    care_id: int,
    rec_in: CareRecordUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "GROOMER", "RECEPTIONIST"]))
):
    rec = _get_record(db, care_id)
    for field, val in rec_in.model_dump(exclude_unset=True).items():
        setattr(rec, field, val)
    db.commit()
    db.refresh(rec)
    return rec

@router.delete("/{care_id}")
def delete_care_record(
    care_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    rec = _get_record(db, care_id)
    db.delete(rec)
    db.commit()
    return {"message": "Đã xóa hồ sơ chăm sóc"}
