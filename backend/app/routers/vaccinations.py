# -*- coding: utf-8 -*-
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import VaccinationReminder, Pet
from ..schemas import VaccinationCreate, VaccinationOut
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/vaccinations", tags=["Vaccination Reminders"])

@router.get("", response_model=List[VaccinationOut])
def get_vaccinations(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(VaccinationReminder).order_by(VaccinationReminder.next_due_date.asc()).all()

@router.post("", response_model=VaccinationOut, status_code=status.HTTP_201_CREATED)
def create_vaccination(
    vac_in: VaccinationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST"]))
):
    pet = db.query(Pet).filter(Pet.pet_id == vac_in.pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Thú cưng không tồn tại")
    vac = VaccinationReminder(**vac_in.dict())
    db.add(vac)
    db.commit()
    db.refresh(vac)
    return vac

@router.put("/{reminder_id}/done", response_model=VaccinationOut)
def mark_vaccination_done(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST"]))
):
    vac = db.query(VaccinationReminder).filter(VaccinationReminder.reminder_id == reminder_id).first()
    if not vac:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch nhắc tiêm")
    vac.status = "DONE"
    db.commit()
    db.refresh(vac)
    return vac


@router.put("/{reminder_id}", response_model=VaccinationOut)
def update_vaccination(reminder_id: int, vac_in: VaccinationCreate, db: Session = Depends(get_db), current_user=Depends(require_role(["ADMIN", "RECEPTIONIST"]))):
    vac = db.query(VaccinationReminder).filter(VaccinationReminder.reminder_id == reminder_id).first()
    if not vac:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch nhắc tiêm")
    if not db.query(Pet).filter(Pet.pet_id == vac_in.pet_id).first():
        raise HTTPException(status_code=404, detail="Thú cưng không tồn tại")
    for field, value in vac_in.model_dump().items():
        setattr(vac, field, value)
    db.commit()
    db.refresh(vac)
    return vac

@router.delete("/{reminder_id}")
def delete_vaccination(reminder_id: int, db: Session = Depends(get_db), current_user=Depends(require_role(["ADMIN"]))):
    vac = db.query(VaccinationReminder).filter(VaccinationReminder.reminder_id == reminder_id).first()
    if not vac:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch nhắc tiêm")
    db.delete(vac)
    db.commit()
    return {"message": "Đã xóa lịch nhắc tiêm"}
