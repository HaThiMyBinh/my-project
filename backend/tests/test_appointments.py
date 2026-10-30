# -*- coding: utf-8 -*-
"""Test lịch hẹn: đặt, chống trùng, đổi lịch, hủy, phân quyền, validate."""


def payload(**over):
    data = {"pet_id": 1, "service_id": 1, "groomer_name": "Thợ Minh",
            "appointment_date": "2099-01-10", "start_time": "09:00", "end_time": "10:00"}
    data.update(over)
    return data


def create(client, headers, **over):
    return client.post("/api/appointments", json=payload(**over), headers=headers)


def test_create_appointment_ok(client, auth):
    r = create(client, auth("letan"))
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "CONFIRMED" and body["groomer_name"] == "Thợ Minh"


def test_overlapping_same_groomer_returns_409(client, auth):
    h = auth("letan")
    assert create(client, h).status_code == 201
    assert create(client, h, start_time="09:30", end_time="10:30").status_code == 409
    assert create(client, h, start_time="08:00", end_time="09:30").status_code == 409   # chồm đầu
    assert create(client, h, start_time="09:15", end_time="09:45").status_code == 409   # nằm trong


def test_adjacent_slots_are_allowed(client, auth):
    h = auth("letan")
    assert create(client, h).status_code == 201
    assert create(client, h, start_time="10:00", end_time="11:00").status_code == 201   # liền kề sau
    assert create(client, h, start_time="08:00", end_time="09:00").status_code == 201   # liền kề trước


def test_different_groomer_or_date_is_allowed(client, auth):
    h = auth("letan")
    assert create(client, h).status_code == 201
    assert create(client, h, groomer_name="Thợ Lan").status_code == 201
    assert create(client, h, appointment_date="2099-01-11").status_code == 201


def test_cancel_frees_the_slot(client, auth):
    h = auth("letan")
    app_id = create(client, h).json()["appointment_id"]
    assert client.delete(f"/api/appointments/{app_id}", headers=h).status_code == 200
    got = client.get("/api/appointments", params={"status": "CANCELLED"}, headers=h).json()
    assert [a["appointment_id"] for a in got] == [app_id]
    assert create(client, h).status_code == 201   # slot đã trống


def test_reschedule_conflict_and_success(client, auth):
    h = auth("letan")
    create(client, h)  # 09-10
    second = create(client, h, start_time="11:00", end_time="12:00").json()["appointment_id"]
    r = client.put(f"/api/appointments/{second}", json={"start_time": "09:30", "end_time": "10:30"}, headers=h)
    assert r.status_code == 409
    r = client.put(f"/api/appointments/{second}", json={"start_time": "10:00", "end_time": "11:00"}, headers=h)
    assert r.status_code == 200 and r.json()["start_time"] == "10:00"


def test_reschedule_to_own_slot_is_not_a_conflict(client, auth):
    h = auth("letan")
    app_id = create(client, h).json()["appointment_id"]
    r = client.put(f"/api/appointments/{app_id}", json={"start_time": "09:00", "end_time": "10:00"}, headers=h)
    assert r.status_code == 200


def test_invalid_time_range_and_format_rejected(client, auth):
    h = auth("letan")
    assert create(client, h, start_time="10:00", end_time="09:00").status_code == 422
    assert create(client, h, start_time="10:00", end_time="10:00").status_code == 422
    assert create(client, h, start_time="25:00", end_time="26:00").status_code == 422
    assert create(client, h, appointment_date="10/01/2099").status_code == 422
    app_id = create(client, h).json()["appointment_id"]
    r = client.put(f"/api/appointments/{app_id}", json={"end_time": "08:00"}, headers=h)
    assert r.status_code == 422


def test_unknown_pet_or_service_returns_404(client, auth):
    h = auth("letan")
    assert create(client, h, pet_id=999).status_code == 404
    assert create(client, h, service_id=999).status_code == 404


def test_permissions(client, auth):
    assert client.post("/api/appointments", json=payload()).status_code == 401          # chưa đăng nhập
    assert create(client, auth("groomer")).status_code == 403                           # groomer không được đặt lịch
    app_id = create(client, auth("letan")).json()["appointment_id"]
    assert client.delete(f"/api/appointments/{app_id}", headers=auth("groomer")).status_code == 403


def test_filter_appointments(client, auth):
    h = auth("letan")
    create(client, h)
    create(client, h, groomer_name="Thợ Lan", appointment_date="2099-02-01")
    assert len(client.get("/api/appointments", params={"date": "2099-02-01"}, headers=h).json()) == 1
    assert len(client.get("/api/appointments", params={"groomer": "Minh"}, headers=h).json()) == 1


def test_complete_appointment_by_each_authorized_role(client, auth):
    for index, role in enumerate(("admin", "letan", "groomer")):
        receptionist = auth("letan")
        appt = create(client, receptionist, appointment_date=f"2099-02-{index+1:02d}").json()
        appointment_id = appt["appointment_id"]
        result = client.patch(f"/api/appointments/{appointment_id}/complete", headers=auth(role))
        assert result.status_code == 200 and result.json()["status"] == "COMPLETED"
        assert client.patch(f"/api/appointments/{appointment_id}/complete", headers=auth(role)).status_code == 409
    assert len(client.get("/api/appointments", params={"status":"COMPLETED"}, headers=auth("letan")).json()) == 3


def test_cannot_complete_cancelled_missing_or_anonymous_appointment(client, auth):
    headers = auth("letan")
    appointment_id = create(client, headers).json()["appointment_id"]
    assert client.patch(f"/api/appointments/{appointment_id}/complete").status_code == 401
    assert client.patch("/api/appointments/999/complete", headers=headers).status_code == 404
    assert client.delete(f"/api/appointments/{appointment_id}", headers=headers).status_code == 200
    assert client.patch(f"/api/appointments/{appointment_id}/complete", headers=auth("groomer")).status_code == 409
    assert client.get("/api/appointments", headers=headers).json()[0]["status"] == "CANCELLED"
