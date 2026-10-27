# -*- coding: utf-8 -*-
"""Test bảo mật, quyền riêng tư, ràng buộc CSDL và nhật ký AI."""
import pytest
from sqlalchemy.exc import IntegrityError

from app import models
from app.routers import ai as ai_router


# ---------------- Đăng nhập ----------------
def test_login_wrong_password_and_unknown_user_give_same_error(client):
    a = client.post("/api/auth/login", json={"username": "admin", "password": "sai"})
    b = client.post("/api/auth/login", json={"username": "khongco", "password": "sai"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()     # không lộ tài khoản nào tồn tại


def test_login_is_locked_after_repeated_failures_then_success_resets(client):
    for _ in range(5):
        assert client.post("/api/auth/login", json={"username": "admin", "password": "sai"}).status_code == 401
    r = client.post("/api/auth/login", json={"username": "admin", "password": "pass1234"})   # đúng mật khẩu nhưng đang bị khóa
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0
    # tài khoản khác không bị ảnh hưởng
    assert client.post("/api/auth/login", json={"username": "letan", "password": "pass1234"}).status_code == 200


def test_successful_login_clears_failure_counter(client):
    for _ in range(4):
        client.post("/api/auth/login", json={"username": "admin", "password": "sai"})
    assert client.post("/api/auth/login", json={"username": "admin", "password": "pass1234"}).status_code == 200
    for _ in range(4):                                     # bộ đếm đã được xóa nên chưa bị khóa
        assert client.post("/api/auth/login", json={"username": "admin", "password": "sai"}).status_code == 401


def test_invalid_or_tampered_token_rejected(client):
    assert client.get("/api/owners", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401
    assert client.get("/api/owners").status_code == 401


# ---------------- Phân quyền dữ liệu ----------------
def test_groomer_sees_masked_owner_contact_but_staff_sees_full(client, auth):
    g = client.get("/api/owners", headers=auth("groomer")).json()[0]
    assert g["full_name"] == "Chị Hoàng Thị Lan"
    assert g["phone"] != "0988123456" and g["phone"].startswith("098") and "*" in g["phone"]
    assert g["address"] is None and g["email"] is None
    one = client.get("/api/owners/1", headers=auth("groomer")).json()
    assert one["address"] is None and "*" in one["phone"]
    full = client.get("/api/owners", headers=auth("letan")).json()[0]
    assert full["phone"] == "0988123456" and full["address"] == "123 Cầu Giấy"


def test_only_admin_reads_ai_logs(client, auth):
    assert client.get("/api/ai/logs", headers=auth("letan")).status_code == 403
    assert client.get("/api/ai/logs", headers=auth("groomer")).status_code == 403
    assert client.get("/api/ai/logs").status_code == 401
    assert client.get("/api/ai/logs", headers=auth("admin")).status_code == 200


# ---------------- Nhật ký AI & giới hạn tần suất ----------------
def test_ai_calls_are_logged_without_content(client, auth, db_session):
    client.post("/api/ai/ask", json={"question": "Chó nhà em đang co giật"}, headers=auth("letan"))
    client.post("/api/ai/ask", json={"question": "Bao lâu nên tắm cho mèo?", "pet_id": 1}, headers=auth("letan"))
    client.post("/api/ai/summary/1", headers=auth("groomer"))
    logs = client.get("/api/ai/logs", headers=auth("admin")).json()
    assert logs["total"] == 3
    assert logs["by_guardrail"] == {"emergency": 1} and logs["need_vet_count"] >= 1
    assert logs["by_source"]["guardrail"] == 1 and logs["by_source"]["fallback"] == 2    # test không có API key
    first = logs["recent"][0]
    assert set(first) == {"created_at", "username", "endpoint", "source", "guardrail", "need_vet", "latency_ms"}
    cols = {c.name for c in models.AILog.__table__.columns}
    assert not ({"question", "response", "content", "answer"} & cols)                     # không lưu nội dung hội thoại


def test_ai_rate_limit_returns_429(client, auth):
    h = auth("letan")
    limit = ai_router.ai_limiter.max_events
    for _ in range(limit):
        assert client.post("/api/ai/ask", json={"question": "Chó nhà em đang co giật"}, headers=h).status_code == 200
    r = client.post("/api/ai/ask", json={"question": "Chó nhà em đang co giật"}, headers=h)
    assert r.status_code == 429 and "Retry-After" in r.headers
    assert client.post("/api/ai/ask", json={"question": "Chó nhà em đang co giật"}, headers=auth("admin")).status_code == 200  # người khác vẫn dùng được
    assert client.get("/api/ai/status", headers=h).status_code == 200                      # /status không tính hạn mức


# ---------------- Ràng buộc CSDL ----------------
def test_database_rejects_invalid_values(db_session):
    bad_rows = [
        models.Appointment(pet_id=1, service_id=1, groomer_name="A", appointment_date="2099-01-01",
                           start_time="09:00", end_time="10:00", status="BOGUS"),
        models.Appointment(pet_id=1, service_id=1, groomer_name="A", appointment_date="2099-01-01",
                           start_time="10:00", end_time="09:00"),
        models.Appointment(pet_id=999, service_id=1, groomer_name="A", appointment_date="2099-01-01",
                           start_time="09:00", end_time="10:00"),                           # khóa ngoại: thú cưng không tồn tại
        models.Service(service_name="Âm", duration_minutes=30, price=-5),
        models.Service(service_name="Không thời lượng", duration_minutes=0, price=5),
    ]
    for row in bad_rows:
        db_session.add(row)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


def test_delete_in_use_service_returns_409_not_500(client, auth):
    h = auth("admin")
    client.post("/api/appointments", json={"pet_id": 1, "service_id": 1, "groomer_name": "A",
                "appointment_date": "2099-01-01", "start_time": "09:00", "end_time": "10:00"}, headers=auth("letan"))
    r = client.delete("/api/services/1", headers=h)
    assert r.status_code == 409
    assert client.get("/api/services", headers=h).status_code == 200                       # phiên vẫn dùng được sau lỗi


def test_invalid_status_and_pet_values_rejected_by_api(client, auth):
    h = auth("letan")
    app_id = client.post("/api/appointments", json={"pet_id": 1, "service_id": 1, "groomer_name": "A",
                         "appointment_date": "2099-01-01", "start_time": "09:00", "end_time": "10:00"}, headers=h).json()["appointment_id"]
    assert client.put(f"/api/appointments/{app_id}", json={"status": "BOGUS"}, headers=h).status_code == 422
    assert client.post("/api/pets", json={"owner_id": 1, "pet_name": "X", "pet_type": "CHO", "weight": 0}, headers=h).status_code == 422
    assert client.post("/api/pets", json={"owner_id": 1, "pet_name": "X", "pet_type": "CHO", "age": 200}, headers=h).status_code == 422


# ---------------- Hệ thống ----------------
def test_health_endpoint_and_security_headers(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok", "database": True}
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY"


def test_cors_not_open_to_arbitrary_origins(client):
    r = client.get("/api/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}
