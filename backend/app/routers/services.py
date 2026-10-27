# -*- coding: utf-8 -*-
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Service, ServicePackageItem
from ..schemas import ServiceCreate, ServiceUpdate, ServiceOut
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/services", tags=["Services"])

@router.get("", response_model=List[ServiceOut])
def get_services(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Service).all()

@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    srv_in: ServiceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    srv = Service(**srv_in.dict())
    db.add(srv)
    db.commit()
    db.refresh(srv)
    return srv

@router.put("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int,
    srv_in: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    srv = db.query(Service).filter(Service.service_id == service_id).first()
    if not srv:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")
    for field, val in srv_in.dict(exclude_unset=True).items():
        setattr(srv, field, val)
    db.commit()
    db.refresh(srv)
    return srv

@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    srv = db.query(Service).filter(Service.service_id == service_id).first()
    if not srv:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ")
    if db.query(ServicePackageItem).filter(ServicePackageItem.service_id == service_id).first():
        raise HTTPException(status_code=409, detail="Dịch vụ đang nằm trong gói dịch vụ, hãy gỡ khỏi gói trước khi xóa")
    db.delete(srv)
    db.commit()
    return {"message": "Đã xóa dịch vụ thành công"}
