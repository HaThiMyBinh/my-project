# -*- coding: utf-8 -*-
"""Test các endpoint /api/ai/* (Gemini được giả lập, không gọi mạng)."""
import pytest

from app import models
from app.services import ai_service as ai


@pytest.fixture()
def fake_gemini(monkeypatch):
    calls = []

    def transport(url, headers, body, timeout):
        calls.append(body)
        return {"candidates": [{"content": {"parts": [{"text": "Nội dung do Gemini giả lập."}]}}]}

    monkeypatch.setattr(ai, "get_client", lambda: ai.GeminiClient(api_key="k", model="m", transport=transport))
    return calls


def add_appointment(db, date="2099-06-01", status="CONFIRMED"):
    db.add(models.Appointment(pet_id=1, service_id=1, groomer_name="Thợ Minh", appointment_date=date,
                              start_time="09:00", end_time="10:00", status=status))
    db.commit()


def test_status_without_key_reports_fallback(client, auth):
    r = client.get("/api/ai/status", headers=auth("admin"))
    assert r.status_code == 200 and r.json()["configured"] is False
    assert "không thay thế" in r.json()["warning"]


def test_all_endpoints_require_login(client):
    assert client.get("/api/ai/status").status_code == 401
    assert client.post("/api/ai/reminder", json={"pet_id": 1}).status_code == 401
    assert client.post("/api/ai/summary/1").status_code == 401
    assert client.post("/api/ai/ask", json={"question": "tắm mèo"}).status_code == 401


def test_reminder_for_upcoming_appointment(client, auth, db_session, fake_gemini):
    add_appointment(db_session)
    r = client.post("/api/ai/reminder", json={"pet_id": 1}, headers=auth("letan"))
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "gemini" and body["warning"] == ai.DISCLAIMER
    prompt = fake_gemini[0]["contents"][0]["parts"][0]["text"]
    assert "Tắm spa" in prompt and "01/06/2099" in prompt and "Chị Hoàng Thị Lan" in prompt
    assert "0988123456" not in prompt and "Cầu Giấy" not in prompt           # không gửi thông tin liên hệ


def test_reminder_ignores_cancelled_and_past_appointments(client, auth, db_session, fake_gemini):
    add_appointment(db_session, date="2099-06-01", status="CANCELLED")
    add_appointment(db_session, date="2000-01-01")
    assert client.post("/api/ai/reminder", json={"pet_id": 1}, headers=auth("letan")).status_code == 404


def test_reminder_vaccination(client, auth, db_session, fake_gemini):
    db_session.add(models.VaccinationReminder(pet_id=1, vaccine_name="Dại", last_date="2025-11-05",
                                              next_due_date="2099-11-05", status="PENDING"))
    db_session.commit()
    r = client.post("/api/ai/reminder", json={"pet_id": 1, "kind": "vaccination"}, headers=auth("letan"))
    assert r.status_code == 200
    assert "Dại" in fake_gemini[0]["contents"][0]["parts"][0]["text"]
    no_vac = client.post("/api/ai/reminder", json={"pet_id": 1, "kind": "vaccination", "reminder_id": 999},
                         headers=auth("letan"))
    assert no_vac.status_code == 404


def test_reminder_fallback_works_without_key(client, auth, db_session):
    add_appointment(db_session)
    body = client.post("/api/ai/reminder", json={"pet_id": 1}, headers=auth("admin")).json()
    assert body["source"] == "fallback" and "Tắm spa" in body["content"]


def test_reminder_validation_and_unknown_pet(client, auth):
    h = auth("admin")
    assert client.post("/api/ai/reminder", json={"pet_id": 999}, headers=h).status_code == 404
    assert client.post("/api/ai/reminder", json={"pet_id": 1, "kind": "bad"}, headers=h).status_code == 422


def test_summary_uses_care_records(client, auth, db_session, fake_gemini):
    db_session.add(models.CareRecord(pet_id=1, weight_after=4.6, skin_condition="Hơi khô", advice="Dưỡng ẩm"))
    db_session.commit()
    r = client.post("/api/ai/summary/1", headers=auth("groomer"))      # groomer cũng dùng được
    assert r.status_code == 200 and r.json()["source"] == "gemini"
    prompt = fake_gemini[0]["contents"][0]["parts"][0]["text"]
    assert "Hơi khô" in prompt and "Da bụng nhạy cảm" in prompt
    assert client.post("/api/ai/summary/999", headers=auth("groomer")).status_code == 404


def test_summary_without_records_or_key(client, auth):
    body = client.post("/api/ai/summary/1", headers=auth("admin")).json()
    assert body["source"] == "fallback" and "Chưa có hồ sơ" in body["content"]


def test_ask_normal_question(client, auth, fake_gemini):
    r = client.post("/api/ai/ask", json={"question": "Bao lâu nên tắm cho mèo?", "pet_id": 1}, headers=auth("admin"))
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "gemini" and body["warning"] == ai.DISCLAIMER and len(fake_gemini) == 1


def test_ask_emergency_never_reaches_gemini(client, auth, fake_gemini):
    r = client.post("/api/ai/ask", json={"question": "Chó nhà em đang co giật"}, headers=auth("admin"))
    body = r.json()
    assert body["guardrail"] == "emergency" and body["need_vet"] is True and "bác sĩ thú y" in body["content"]
    assert fake_gemini == []


def test_ask_prescription_request_is_refused(client, auth, fake_gemini):
    body = client.post("/api/ai/ask", json={"question": "Cho mèo uống paracetamol bao nhiêu mg?"},
                       headers=auth("admin")).json()
    assert body["guardrail"] == "out_of_scope" and fake_gemini == []


def test_ask_validation(client, auth):
    h = auth("admin")
    assert client.post("/api/ai/ask", json={"question": "  a "}, headers=h).status_code == 422
    assert client.post("/api/ai/ask", json={"question": "x" * 501}, headers=h).status_code == 422
    assert client.post("/api/ai/ask", json={"question": "tắm mèo", "pet_id": 999}, headers=h).status_code == 404


def test_ask_without_key_returns_safe_message(client, auth):
    body = client.post("/api/ai/ask", json={"question": "Bao lâu nên tắm cho mèo?"}, headers=auth("admin")).json()
    assert body["source"] == "fallback" and body["warning"] == ai.DISCLAIMER


def test_global_error_handler_does_not_leak_details(client, auth, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("SECRET-DB-PATH")
    monkeypatch.setattr(ai, "answer_question", boom)
    from fastapi.testclient import TestClient
    from app.main import app
    safe_client = TestClient(app, raise_server_exceptions=False)
    r = safe_client.post("/api/ai/ask", json={"question": "Bao lâu nên tắm cho mèo?"}, headers=auth("admin"))
    assert r.status_code == 500 and "SECRET-DB-PATH" not in r.text
