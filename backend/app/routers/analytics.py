# -*- coding: utf-8 -*-
from collections import defaultdict
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import require_role
from ..database import get_db
from ..models import (Appointment, Invoice, InvoiceItem, Owner, Payment, Pet, Service,
                      VaccinationReminder)
from ..schemas import DashboardStats

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Dashboard"])


def _revenue_and_debt(db: Session):
    """Doanh thu = tiền đã THU thực tế (bỏ hóa đơn hủy). Công nợ = phần còn thiếu của hóa đơn chưa hủy."""
    revenue = (db.query(func.sum(Payment.amount)).join(Invoice, Payment.invoice_id == Invoice.invoice_id)
               .filter(Invoice.status != "CANCELLED").scalar() or 0.0)
    debt = 0.0
    for inv in db.query(Invoice).filter(Invoice.status != "CANCELLED").all():
        debt += max(0.0, inv.final_amount - sum(p.amount for p in inv.payments))
    return round(revenue, 2), round(debt, 2)


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user=Depends(require_role(["ADMIN", "RECEPTIONIST"]))):
    total_owners = db.query(Owner).count()
    total_pets = db.query(Pet).count()
    total_appointments = db.query(Appointment).count()
    total_revenue, total_debt = _revenue_and_debt(db)

    # Retention Rate: chủ nuôi có >= 2 lịch hẹn / chủ nuôi có >= 1 lịch hẹn
    customer_app_counts = (db.query(Pet.owner_id, func.count(Appointment.appointment_id))
                           .join(Appointment, Pet.pet_id == Appointment.pet_id)
                           .group_by(Pet.owner_id).all())
    total_active_cust = len(customer_app_counts)
    repeat_cust = sum(1 for c in customer_app_counts if c[1] >= 2)
    retention_rate = round((repeat_cust / total_active_cust * 100), 1) if total_active_cust > 0 else 0.0

    pending_apps = db.query(Appointment).filter(Appointment.status == "CONFIRMED").count()
    upcoming_vacs = db.query(VaccinationReminder).filter(VaccinationReminder.status == "PENDING").count()

    return {
        "total_owners": total_owners,
        "total_pets": total_pets,
        "total_appointments": total_appointments,
        "total_revenue": total_revenue,
        "retention_rate": retention_rate,
        "pending_appointments": pending_apps,
        "upcoming_vaccines": upcoming_vacs,
        "total_debt": total_debt,
    }


@router.get("/services")
def service_stats(db: Session = Depends(get_db), current_user=Depends(require_role(["ADMIN", "RECEPTIONIST"]))):
    """Thống kê theo dịch vụ: số lượt đặt (không tính lịch hủy), số lượt hoàn thành, doanh thu ghi trên hóa đơn."""
    rows = []
    for srv in db.query(Service).all():
        booked = db.query(Appointment).filter(Appointment.service_id == srv.service_id,
                                              Appointment.status != "CANCELLED").count()
        done = db.query(Appointment).filter(Appointment.service_id == srv.service_id,
                                            Appointment.status == "COMPLETED").count()
        revenue = (db.query(func.sum(InvoiceItem.subtotal))
                   .join(Invoice, InvoiceItem.invoice_id == Invoice.invoice_id)
                   .filter(InvoiceItem.service_id == srv.service_id, Invoice.status != "CANCELLED")
                   .scalar() or 0.0)
        rows.append({"service_id": srv.service_id, "service_name": srv.service_name,
                     "booked_count": booked, "completed_count": done, "revenue": revenue})
    rows.sort(key=lambda r: (-r["booked_count"], -r["revenue"]))
    return rows


@router.get("/revenue")
def revenue_by_period(period: str = Query("month", pattern="^(day|month)$"),
                      db: Session = Depends(get_db), current_user=Depends(require_role(["ADMIN", "RECEPTIONIST"]))):
    """Doanh thu đã thu theo ngày hoặc theo tháng."""
    fmt = "%Y-%m-%d" if period == "day" else "%Y-%m"
    totals = defaultdict(float)
    q = db.query(Payment).join(Invoice, Payment.invoice_id == Invoice.invoice_id).filter(Invoice.status != "CANCELLED")
    for p in q.all():
        totals[p.payment_date.strftime(fmt)] += p.amount
    return [{"period": k, "revenue": round(v, 2)} for k, v in sorted(totals.items())]
