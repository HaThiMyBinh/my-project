# -*- coding: utf-8 -*-
"""Test hóa đơn: tính tiền, giảm giá, thanh toán, validate, phân quyền, doanh thu."""
from app import models


def invoice(**over):
    data = {"owner_id": 1, "discount": 0, "payment_method": "TIEN_MAT",
            "items": [{"service_id": 1, "quantity": 2, "unit_price": 200000},
                      {"service_id": 2, "quantity": 1, "unit_price": 150000}]}
    data.update(over)
    return data


def test_create_invoice_calculates_totals(client, auth):
    r = client.post("/api/invoices", json=invoice(discount=50000), headers=auth("letan"))
    assert r.status_code == 201
    body = r.json()
    assert body["total_amount"] == 550000
    assert body["discount"] == 50000
    assert body["final_amount"] == 500000
    assert body["status"] == "PAID"
    assert len(body["items"]) == 2
    assert {i["subtotal"] for i in body["items"]} == {400000, 150000}


def test_discount_larger_than_subtotal_gives_zero(client, auth):
    r = client.post("/api/invoices", json=invoice(discount=9_999_999), headers=auth("admin"))
    assert r.status_code == 201
    assert r.json()["final_amount"] == 0


def test_payment_record_is_created(client, auth, db_session):
    r = client.post("/api/invoices", json=invoice(payment_method="CHUYEN_KHOAN"), headers=auth("letan"))
    inv_id = r.json()["invoice_id"]
    pay = db_session.query(models.Payment).filter(models.Payment.invoice_id == inv_id).one()
    assert pay.payment_method == "CHUYEN_KHOAN"
    assert pay.amount == r.json()["final_amount"]


def test_invalid_invoice_payloads_rejected(client, auth):
    h = auth("letan")
    bad_qty = invoice(items=[{"service_id": 1, "quantity": 0, "unit_price": 100}])
    neg_qty = invoice(items=[{"service_id": 1, "quantity": -3, "unit_price": 100}])
    neg_price = invoice(items=[{"service_id": 1, "quantity": 1, "unit_price": -100}])
    for bad in (bad_qty, neg_qty, neg_price, invoice(discount=-1), invoice(items=[])):
        assert client.post("/api/invoices", json=bad, headers=h).status_code == 422


def test_unknown_owner_returns_404(client, auth):
    assert client.post("/api/invoices", json=invoice(owner_id=999), headers=auth("letan")).status_code == 404


def test_permissions(client, auth):
    assert client.post("/api/invoices", json=invoice()).status_code == 401
    assert client.post("/api/invoices", json=invoice(), headers=auth("groomer")).status_code == 403


def test_dashboard_revenue_matches_invoices(client, auth):
    client.post("/api/invoices", json=invoice(), headers=auth("letan"))                    # 550000
    client.post("/api/invoices", json=invoice(discount=50000), headers=auth("letan"))      # 500000
    stats = client.get("/api/analytics/dashboard", headers=auth("admin")).json()
    assert stats["total_revenue"] == 1_050_000
    assert stats["total_owners"] == 1 and stats["total_pets"] == 1


def test_retention_rate(client, auth):
    h = auth("letan")
    for d in ("2099-03-01", "2099-03-02"):                         # chủ nuôi #1 có 2 lịch -> khách quay lại
        client.post("/api/appointments", json={"pet_id": 1, "service_id": 1, "groomer_name": "A",
                    "appointment_date": d, "start_time": "09:00", "end_time": "10:00"}, headers=h)
    stats = client.get("/api/analytics/dashboard", headers=h).json()
    assert stats["retention_rate"] == 100.0


# ---------------- Công nợ & thanh toán nhiều lần ----------------
def test_partial_payment_creates_debt(client, auth):
    r = client.post("/api/invoices", json=invoice(paid_amount=200000), headers=auth("letan"))
    body = r.json()
    assert r.status_code == 201 and body["final_amount"] == 550000
    assert body["status"] == "PARTIAL" and body["paid_amount"] == 200000 and body["remaining"] == 350000
    assert len(body["payments"]) == 1


def test_zero_paid_is_unpaid_and_has_no_payment_row(client, auth):
    body = client.post("/api/invoices", json=invoice(paid_amount=0), headers=auth("letan")).json()
    assert body["status"] == "UNPAID" and body["paid_amount"] == 0 and body["payments"] == []


def test_overpay_on_create_rejected(client, auth):
    assert client.post("/api/invoices", json=invoice(paid_amount=999_999_999), headers=auth("letan")).status_code == 422


def test_add_payments_until_paid(client, auth):
    h = auth("letan")
    inv_id = client.post("/api/invoices", json=invoice(paid_amount=100000), headers=h).json()["invoice_id"]
    r = client.post(f"/api/invoices/{inv_id}/payments", json={"amount": 200000, "payment_method": "CHUYEN_KHOAN",
                                                               "transaction_code": "QR-1"}, headers=h)
    assert r.status_code == 201
    assert r.json()["status"] == "PARTIAL" and r.json()["remaining"] == 250000
    r = client.post(f"/api/invoices/{inv_id}/payments", json={"amount": 250000}, headers=h)
    assert r.json()["status"] == "PAID" and r.json()["remaining"] == 0 and len(r.json()["payments"]) == 3
    # đã đủ tiền -> không thu thêm
    assert client.post(f"/api/invoices/{inv_id}/payments", json={"amount": 1}, headers=h).status_code == 409


def test_payment_validation(client, auth):
    h = auth("letan")
    inv_id = client.post("/api/invoices", json=invoice(paid_amount=100000), headers=h).json()["invoice_id"]
    assert client.post(f"/api/invoices/{inv_id}/payments", json={"amount": 0}, headers=h).status_code == 422
    assert client.post(f"/api/invoices/{inv_id}/payments", json={"amount": -5}, headers=h).status_code == 422
    assert client.post(f"/api/invoices/{inv_id}/payments", json={"amount": 450001}, headers=h).status_code == 422
    assert client.post("/api/invoices/999/payments", json={"amount": 10}, headers=h).status_code == 404
    assert client.post(f"/api/invoices/{inv_id}/payments", json={"amount": 10}, headers=auth("groomer")).status_code == 403


def test_cancelled_invoice_excluded_from_revenue_and_debt(client, auth):
    h = auth("admin")
    a = client.post("/api/invoices", json=invoice(paid_amount=100000), headers=h).json()["invoice_id"]   # nợ 450000
    client.post("/api/invoices", json=invoice(), headers=h)                                               # thu đủ 550000
    stats = client.get("/api/analytics/dashboard", headers=h).json()
    assert stats["total_revenue"] == 650000 and stats["total_debt"] == 450000
    assert client.post(f"/api/invoices/{a}/cancel", headers=auth("letan")).status_code == 403      # chỉ ADMIN
    assert client.post(f"/api/invoices/{a}/cancel", headers=h).json()["status"] == "CANCELLED"
    stats = client.get("/api/analytics/dashboard", headers=h).json()
    assert stats["total_revenue"] == 550000 and stats["total_debt"] == 0
    assert client.post(f"/api/invoices/{a}/payments", json={"amount": 10}, headers=h).status_code == 409


def test_unit_price_defaults_to_service_price_and_unknown_service_404(client, auth):
    h = auth("letan")
    body = client.post("/api/invoices", json=invoice(items=[{"service_id": 1, "quantity": 3}]), headers=h).json()
    assert body["total_amount"] == 600000 and body["items"][0]["unit_price"] == 200000
    bad = invoice(items=[{"service_id": 999, "quantity": 1}])
    assert client.post("/api/invoices", json=bad, headers=h).status_code == 404


def test_list_filter_and_detail(client, auth):
    h = auth("letan")
    client.post("/api/invoices", json=invoice(), headers=h)
    inv_id = client.post("/api/invoices", json=invoice(paid_amount=10), headers=h).json()["invoice_id"]
    assert len(client.get("/api/invoices", headers=h).json()) == 2
    partial = client.get("/api/invoices", params={"status": "PARTIAL"}, headers=h).json()
    assert [i["invoice_id"] for i in partial] == [inv_id]
    assert client.get(f"/api/invoices/{inv_id}", headers=h).json()["remaining"] == 549990
    assert client.get("/api/invoices/999", headers=h).status_code == 404


# ---------------- Thống kê ----------------
def test_service_and_revenue_statistics(client, auth):
    h = auth("letan")
    for d in ("2099-03-01", "2099-03-02"):
        client.post("/api/appointments", json={"pet_id": 1, "service_id": 1, "groomer_name": "A",
                    "appointment_date": d, "start_time": "09:00", "end_time": "10:00"}, headers=h)
    client.post("/api/invoices", json=invoice(), headers=h)
    stats = {s["service_id"]: s for s in client.get("/api/analytics/services", headers=h).json()}
    assert stats[1]["booked_count"] == 2 and stats[2]["booked_count"] == 0
    assert stats[1]["revenue"] == 400000 and stats[2]["revenue"] == 150000
    months = client.get("/api/analytics/revenue", params={"period": "month"}, headers=h).json()
    assert len(months) == 1 and months[0]["revenue"] == 550000
    assert client.get("/api/analytics/revenue", params={"period": "year"}, headers=h).status_code == 422
