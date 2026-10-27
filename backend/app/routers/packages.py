# -*- coding: utf-8 -*-
"""Gói dịch vụ chăm sóc (combo nhiều dịch vụ với giá ưu đãi)."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models import Service, ServicePackage, ServicePackageItem
from ..schemas import PackageCreate, PackageOut, PackageUpdate

router = APIRouter(prefix="/api/packages", tags=["Service Packages"])


def _to_out(pkg: ServicePackage) -> dict:
    items = [{
        "service_id": it.service_id,
        "service_name": it.service.service_name if it.service else "(đã xóa)",
        "quantity": it.quantity,
        "unit_price": it.service.price if it.service else 0.0,
    } for it in pkg.items]
    original = sum(i["quantity"] * i["unit_price"] for i in items)
    return {
        "package_id": pkg.package_id, "package_name": pkg.package_name, "description": pkg.description,
        "price": pkg.price, "is_active": bool(pkg.is_active), "items": items,
        "original_price": original, "saving": max(0.0, original - pkg.price),
    }


def _validate_items(db: Session, items) -> None:
    seen = set()
    for it in items:
        if it.service_id in seen:
            raise HTTPException(status_code=422, detail="Một dịch vụ chỉ xuất hiện một lần trong gói (hãy tăng số lượng)")
        seen.add(it.service_id)
        if not db.query(Service).filter(Service.service_id == it.service_id).first():
            raise HTTPException(status_code=404, detail=f"Dịch vụ #{it.service_id} không tồn tại")


def _get(db: Session, package_id: int) -> ServicePackage:
    pkg = db.query(ServicePackage).filter(ServicePackage.package_id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Không tìm thấy gói dịch vụ")
    return pkg


@router.get("", response_model=List[PackageOut])
def list_packages(active_only: bool = False, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(ServicePackage)
    if active_only:
        q = q.filter(ServicePackage.is_active == True)  # noqa: E712
    return [_to_out(p) for p in q.order_by(ServicePackage.package_id).all()]


@router.get("/{package_id}", response_model=PackageOut)
def get_package(package_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return _to_out(_get(db, package_id))


@router.post("", response_model=PackageOut, status_code=status.HTTP_201_CREATED)
def create_package(pkg_in: PackageCreate, db: Session = Depends(get_db),
                   current_user=Depends(require_role(["ADMIN"]))):
    _validate_items(db, pkg_in.items)
    pkg = ServicePackage(package_name=pkg_in.package_name, description=pkg_in.description,
                         price=pkg_in.price, is_active=pkg_in.is_active)
    pkg.items = [ServicePackageItem(service_id=i.service_id, quantity=i.quantity) for i in pkg_in.items]
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return _to_out(pkg)


@router.put("/{package_id}", response_model=PackageOut)
def update_package(package_id: int, pkg_in: PackageUpdate, db: Session = Depends(get_db),
                   current_user=Depends(require_role(["ADMIN"]))):
    pkg = _get(db, package_id)
    data = pkg_in.model_dump(exclude_unset=True)
    new_items = data.pop("items", None)
    if new_items is not None:
        _validate_items(db, pkg_in.items)
        pkg.items = [ServicePackageItem(service_id=i["service_id"], quantity=i["quantity"]) for i in new_items]
    for field, val in data.items():
        setattr(pkg, field, val)
    db.commit()
    db.refresh(pkg)
    return _to_out(pkg)


@router.delete("/{package_id}")
def delete_package(package_id: int, db: Session = Depends(get_db),
                   current_user=Depends(require_role(["ADMIN"]))):
    pkg = _get(db, package_id)
    db.delete(pkg)
    db.commit()
    return {"message": "Đã xóa gói dịch vụ"}
