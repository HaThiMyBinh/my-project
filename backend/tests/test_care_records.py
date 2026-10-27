# -*- coding: utf-8 -*-
"""Test hồ sơ chăm sóc."""


def record(**over):
    data = {"pet_id": 1, "weight_after": 4.6, "skin_condition": "Hơi khô", "behavior_notes": "Ngoan", "advice": "Dưỡng ẩm"}
    data.update(over)
    return data


def test_create_and_list_records(client, auth):
    r = client.post("/api/care-records", json=record(), headers=auth("groomer"))
    assert r.status_code == 201 and r.json()["skin_condition"] == "Hơi khô"
    rows = client.get("/api/care-records", params={"pet_id": 1}, headers=auth("letan")).json()
    assert len(rows) == 1 and rows[0]["pet_id"] == 1


def test_record_with_appointment_marks_it_completed(client, auth):
    h = auth("letan")
    app_id = client.post("/api/appointments", json={"pet_id": 1, "service_id": 1, "groomer_name": "A",
                         "appointment_date": "2099-05-01", "start_time": "09:00", "end_time": "10:00"},
                         headers=h).json()["appointment_id"]
    r = client.post("/api/care-records", json=record(appointment_id=app_id), headers=auth("groomer"))
    assert r.status_code == 201
    done = client.get("/api/appointments", params={"status": "COMPLETED"}, headers=h).json()
    assert [a["appointment_id"] for a in done] == [app_id]


def test_unknown_pet_returns_404(client, auth):
    assert client.post("/api/care-records", json=record(pet_id=999), headers=auth("admin")).status_code == 404


def test_requires_login(client):
    assert client.post("/api/care-records", json=record()).status_code == 401
    assert client.get("/api/care-records").status_code == 401


def test_filter_by_pet(client, auth, db_session):
    from app import models
    db_session.add(models.Pet(owner_id=1, pet_name="Bé Đậu", pet_type="CHO", weight=3.8))
    db_session.commit()
    client.post("/api/care-records", json=record(pet_id=1), headers=auth("admin"))
    client.post("/api/care-records", json=record(pet_id=2), headers=auth("admin"))
    assert len(client.get("/api/care-records", params={"pet_id": 2}, headers=auth("admin")).json()) == 1
    assert len(client.get("/api/care-records", headers=auth("admin")).json()) == 2


def test_update_record(client, auth):
    rid = client.post("/api/care-records", json=record(), headers=auth("groomer")).json()["care_id"]
    r = client.put(f"/api/care-records/{rid}", json={"skin_condition": "Đã đỡ khô", "weight_after": 4.7},
                   headers=auth("groomer"))
    assert r.status_code == 200
    body = r.json()
    assert body["skin_condition"] == "Đã đỡ khô" and body["weight_after"] == 4.7
    assert body["behavior_notes"] == "Ngoan" and body["pet_id"] == 1      # trường không gửi giữ nguyên


def test_update_validation_and_404(client, auth):
    rid = client.post("/api/care-records", json=record(), headers=auth("admin")).json()["care_id"]
    assert client.put(f"/api/care-records/{rid}", json={"weight_after": -1}, headers=auth("admin")).status_code == 422
    assert client.put("/api/care-records/999", json={"advice": "x"}, headers=auth("admin")).status_code == 404
    assert client.put(f"/api/care-records/{rid}", json={"advice": "x"}).status_code == 401


def test_delete_record_admin_only(client, auth):
    rid = client.post("/api/care-records", json=record(), headers=auth("groomer")).json()["care_id"]
    assert client.delete(f"/api/care-records/{rid}", headers=auth("groomer")).status_code == 403
    assert client.delete(f"/api/care-records/{rid}", headers=auth("letan")).status_code == 403
    assert client.delete(f"/api/care-records/{rid}", headers=auth("admin")).status_code == 200
    assert client.get(f"/api/care-records/{rid}", headers=auth("admin")).status_code == 404
    assert client.delete(f"/api/care-records/{rid}", headers=auth("admin")).status_code == 404
