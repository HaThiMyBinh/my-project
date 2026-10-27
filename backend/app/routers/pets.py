# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Pet, Owner
from ..schemas import PetCreate, PetUpdate, PetOut
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/pets", tags=["Pets"])

@router.get("", response_model=List[PetOut])
def get_pets(
    search: Optional[str] = Query(None, description="Tìm theo tên thú cưng hoặc giống"),
    pet_type: Optional[str] = Query(None, description="Lọc theo loài (CHO, MEO)"),
    owner_id: Optional[int] = Query(None, description="Lọc theo chủ nuôi"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Pet)
    if search:
        query = query.filter((Pet.pet_name.ilike(f"%{search}%")) | (Pet.breed.ilike(f"%{search}%")))
    if pet_type:
        query = query.filter(Pet.pet_type == pet_type.upper())
    if owner_id:
        query = query.filter(Pet.owner_id == owner_id)
    return query.order_by(Pet.created_at.desc()).all()

@router.get("/{pet_id}", response_model=PetOut)
def get_pet(pet_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    pet = db.query(Pet).filter(Pet.pet_id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Không tìm thấy thú cưng")
    return pet

@router.post("", response_model=PetOut, status_code=status.HTTP_201_CREATED)
def create_pet(
    pet_in: PetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST"]))
):
    owner = db.query(Owner).filter(Owner.owner_id == pet_in.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Chủ nuôi không tồn tại")
    pet = Pet(**pet_in.dict())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet

@router.put("/{pet_id}", response_model=PetOut)
def update_pet(
    pet_id: int,
    pet_in: PetUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST"]))
):
    pet = db.query(Pet).filter(Pet.pet_id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Không tìm thấy thú cưng")
    if pet_in.owner_id is not None and not db.query(Owner).filter(Owner.owner_id == pet_in.owner_id).first():
        raise HTTPException(status_code=404, detail="Chủ nuôi không tồn tại")
    for field, val in pet_in.dict(exclude_unset=True).items():
        setattr(pet, field, val)
    db.commit()
    db.refresh(pet)
    return pet

@router.delete("/{pet_id}")
def delete_pet(
    pet_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    pet = db.query(Pet).filter(Pet.pet_id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Không tìm thấy thú cưng")
    db.delete(pet)
    db.commit()
    return {"message": "Đã xóa thú cưng thành công"}
