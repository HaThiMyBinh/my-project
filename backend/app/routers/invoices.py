# -*- coding: utf-8 -*-
"""Hóa đơn, thanh toán nhiều lần và theo dõi công nợ.

Trạng thái hóa đơn:
  PAID      đã thu đủ
  PARTIAL   đã thu một phần (còn nợ)
  UNPAID    chưa thu đồng nào
  CANCELLED đã hủy (không tính vào doanh thu và công nợ)
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models import Appointment, Invoice, InvoiceItem, Owner, Payment, Service
from ..schemas import InvoiceCreate, InvoiceOut, PaymentCreate

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

EPS = 0.005


def paid_total(inv: Invoice) -> float:
    return round(sum(p.amount for p in inv.payments), 2)


def compute_status(final_amount: float, paid: float) -> str:
    if paid + EPS >= final_amount:
        return "PAID"
    return "PARTIAL" if paid > EPS else "UNPAID"


def to_out(inv: Invoice) -> dict:
    paid = paid_total(inv)
    cancelled = inv.status == "CANCELLED"
    return {
        "invoice_id": inv.invoice_id, "owner_id": inv.owner_id, "appointment_id": inv.appointment_id,
        "created_at": inv.created_at, "total_amount": inv.total_amount, "discount": inv.discount,
        "final_amount": inv.final_amount, "status": inv.status, "paid_amount": paid,
        "remaining": 0.0 if cancelled else max(0.0, round(inv.final_amount - paid, 2)),
        "items": [{"item_id": i.item_id, "service_id": i.service_id, "quantity": i.quantity,
                   "unit_price": i.unit_price, "subtotal": i.subtotal} for i in inv.items],
        "payments": [{"payment_id": p.payment_id, "payment_method": p.payment_method,
                      "payment_date": p.payment_date, "amount": p.amount,
                      "transaction_code": p.transaction_code} for p in inv.payments],
    }


def _get(db: Session, invoice_id: int) -> Invoice:
    inv = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")
    return inv


@router.get("", response_model=List[InvoiceOut])
def get_invoices(
    status_filter: Optional[str] = Query(None, alias="status", description="PAID, PARTIAL, UNPAID, CANCELLED"),
    owner_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN", "RECEPTIONIST"])),
):
    q = db.query(Invoice)
    if status_filter:
        q = q.filter(Invoice.status == status_filter.upper())
    if owner_id:
        q = q.filter(Invoice.owner_id == owner_id)
    return [to_out(i) for i in q.order_by(Invoice.created_at.desc(), Invoice.invoice_id.desc()).all()]


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), current_user=Depends(require_role(["ADMIN", "RECEPTIONIST"]))):
    return to_out(_get(db, invoice_id))


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    inv_in: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN", "RECEPTIONIST"])),
):
    owner = db.query(Owner).filter(Owner.owner_id == inv_in.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Chủ nuôi không tồn tại")
    if inv_in.appointment_id and not db.query(Appointment).filter(
            Appointment.appointment_id == inv_in.appointment_id).first():
        raise HTTPException(status_code=404, detail="Lịch hẹn không tồn tại")

    lines = []
    for it in inv_in.items:
        srv = db.query(Service).filter(Service.service_id == it.service_id).first()
        if not srv:
            raise HTTPException(status_code=404, detail=f"Dịch vụ #{it.service_id} không tồn tại")
        price = it.unit_price if it.unit_price is not None else srv.price
        lines.append((it, price))

    subtotal = sum(it.quantity * price for it, price in lines)
    final_total = max(0.0, subtotal - inv_in.discount)
    paid = final_total if inv_in.paid_amount is None else inv_in.paid_amount
    if paid > final_total + EPS:
        raise HTTPException(status_code=422, detail="Số tiền thanh toán vượt quá tổng hóa đơn")

    invoice = Invoice(owner_id=inv_in.owner_id, appointment_id=inv_in.appointment_id, total_amount=subtotal,
                      discount=inv_in.discount, final_amount=final_total,
                      status=compute_status(final_total, paid))
    db.add(invoice)
    db.flush()
    for it, price in lines:
        db.add(InvoiceItem(invoice_id=invoice.invoice_id, service_id=it.service_id, quantity=it.quantity,
                           unit_price=price, subtotal=it.quantity * price))
    if paid > EPS:
        db.add(Payment(invoice_id=invoice.invoice_id, payment_method=inv_in.payment_method, amount=paid))
    db.commit()
    db.refresh(invoice)
    return to_out(invoice)


@router.post("/{invoice_id}/payments", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def add_payment(
    invoice_id: int,
    pay_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN", "RECEPTIONIST"])),
):
    inv = _get(db, invoice_id)
    if inv.status == "CANCELLED":
        raise HTTPException(status_code=409, detail="Hóa đơn đã bị hủy, không thể thu tiền")
    remaining = round(inv.final_amount - paid_total(inv), 2)
    if remaining <= EPS:
        raise HTTPException(status_code=409, detail="Hóa đơn đã thanh toán đủ")
    if pay_in.amount > remaining + EPS:
        raise HTTPException(status_code=422, detail=f"Số tiền vượt quá số còn nợ ({remaining:,.0f} đ)")
    db.add(Payment(invoice_id=inv.invoice_id, payment_method=pay_in.payment_method, amount=pay_in.amount,
                   transaction_code=pay_in.transaction_code))
    db.flush()
    db.refresh(inv)
    inv.status = compute_status(inv.final_amount, paid_total(inv))
    db.commit()
    db.refresh(inv)
    return to_out(inv)


@router.post("/{invoice_id}/cancel", response_model=InvoiceOut)
def cancel_invoice(invoice_id: int, db: Session = Depends(get_db),
                   current_user=Depends(require_role(["ADMIN"]))):
    inv = _get(db, invoice_id)
    inv.status = "CANCELLED"
    db.commit()
    db.refresh(inv)
    return to_out(inv)
