# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Owner
from ..schemas import OwnerCreate, OwnerUpdate, OwnerOut
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/owners", tags=["Owners"])

def _mask_phone(phone: str) -> str:
    return phone[:3] + "*" * max(0, len(phone) - 6) + phone[-3:] if len(phone) > 6 else "***"

def _for_role(owner: Owner, user) -> dict:
    """Nguyên tắc tối thiểu quyền: thợ chăm sóc chỉ cần tên và SĐT đã che, không thấy địa chỉ/email."""
    data = {"owner_id": owner.owner_id, "full_name": owner.full_name, "phone": owner.phone,
            "address": owner.address, "email": owner.email, "created_at": owner.created_at}
    if user.role == "GROOMER":
        data.update(phone=_mask_phone(owner.phone), address=None, email=None)
    return data

@router.get("", response_model=List[OwnerOut])
def get_owners(
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc số điện thoại"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Owner)
    if search:
        query = query.filter(
            (Owner.full_name.ilike(f"%{search}%")) | (Owner.phone.ilike(f"%{search}%"))
        )
    return [_for_role(o, current_user) for o in query.order_by(Owner.created_at.desc()).all()]

@router.get("/{owner_id}", response_model=OwnerOut)
def get_owner(owner_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    owner = db.query(Owner).filter(Owner.owner_id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Không tìm thấy chủ nuôi")
    return _for_role(owner, current_user)

@router.post("", response_model=OwnerOut, status_code=status.HTTP_201_CREATED)
def create_owner(
    owner_in: OwnerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST"]))
):
    existing = db.query(Owner).filter(Owner.phone == owner_in.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Số điện thoại này đã được đăng ký cho chủ nuôi khác")
    owner = Owner(**owner_in.dict())
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner

@router.put("/{owner_id}", response_model=OwnerOut)
def update_owner(
    owner_id: int,
    owner_in: OwnerUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "RECEPTIONIST"]))
):
    owner = db.query(Owner).filter(Owner.owner_id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Không tìm thấy chủ nuôi")
    for field, val in owner_in.dict(exclude_unset=True).items():
        setattr(owner, field, val)
    db.commit()
    db.refresh(owner)
    return owner

@router.delete("/{owner_id}")
def delete_owner(
    owner_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    owner = db.query(Owner).filter(Owner.owner_id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Không tìm thấy chủ nuôi")
    db.delete(owner)
    db.commit()
    return {"message": "Đã xóa chủ nuôi thành công"}
