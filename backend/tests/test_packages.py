# -*- coding: utf-8 -*-
"""Test gói dịch vụ."""


def pkg(**over):
    data = {"package_name": "Gói Spa Toàn Diện", "description": "Combo", "price": 300000,
            "items": [{"service_id": 1, "quantity": 1}, {"service_id": 2, "quantity": 1}]}   # lẻ: 200000 + 150000
    data.update(over)
    return data


def test_admin_creates_package_with_saving(client, auth):
    r = client.post("/api/packages", json=pkg(), headers=auth("admin"))
    assert r.status_code == 201
    body = r.json()
    assert body["original_price"] == 350000 and body["saving"] == 50000 and body["is_active"] is True
    assert {i["service_name"] for i in body["items"]} == {"Tắm spa", "Cắt tỉa lông"}


def test_list_and_get_package(client, auth):
    pid = client.post("/api/packages", json=pkg(), headers=auth("admin")).json()["package_id"]
    assert len(client.get("/api/packages", headers=auth("groomer")).json()) == 1
    assert client.get(f"/api/packages/{pid}", headers=auth("letan")).json()["package_name"] == "Gói Spa Toàn Diện"
    assert client.get("/api/packages/999", headers=auth("admin")).status_code == 404


def test_only_admin_can_modify(client, auth):
    assert client.post("/api/packages", json=pkg(), headers=auth("letan")).status_code == 403
    assert client.post("/api/packages", json=pkg()).status_code == 401
    pid = client.post("/api/packages", json=pkg(), headers=auth("admin")).json()["package_id"]
    assert client.put(f"/api/packages/{pid}", json={"price": 1}, headers=auth("letan")).status_code == 403
    assert client.delete(f"/api/packages/{pid}", headers=auth("letan")).status_code == 403


def test_validation(client, auth):
    h = auth("admin")
    assert client.post("/api/packages", json=pkg(items=[]), headers=h).status_code == 422
    assert client.post("/api/packages", json=pkg(price=-1), headers=h).status_code == 422
    assert client.post("/api/packages", json=pkg(package_name="a"), headers=h).status_code == 422
    assert client.post("/api/packages", json=pkg(items=[{"service_id": 1, "quantity": 0}]), headers=h).status_code == 422
    assert client.post("/api/packages", json=pkg(items=[{"service_id": 999, "quantity": 1}]), headers=h).status_code == 404
    dup = pkg(items=[{"service_id": 1, "quantity": 1}, {"service_id": 1, "quantity": 2}])
    assert client.post("/api/packages", json=dup, headers=h).status_code == 422


def test_update_price_items_and_deactivate(client, auth):
    h = auth("admin")
    pid = client.post("/api/packages", json=pkg(), headers=h).json()["package_id"]
    r = client.put(f"/api/packages/{pid}", json={"price": 250000, "items": [{"service_id": 1, "quantity": 2}]}, headers=h)
    assert r.status_code == 200
    assert r.json()["price"] == 250000 and r.json()["original_price"] == 400000 and len(r.json()["items"]) == 1
    client.put(f"/api/packages/{pid}", json={"is_active": False}, headers=h)
    assert client.get("/api/packages", params={"active_only": True}, headers=h).json() == []
    assert len(client.get("/api/packages", headers=h).json()) == 1


def test_delete_package_and_service_in_package_is_protected(client, auth):
    h = auth("admin")
    pid = client.post("/api/packages", json=pkg(), headers=h).json()["package_id"]
    assert client.delete("/api/services/1", headers=h).status_code == 409      # đang nằm trong gói
    assert client.delete(f"/api/packages/{pid}", headers=h).status_code == 200
    assert client.get(f"/api/packages/{pid}", headers=h).status_code == 404
    assert client.delete("/api/services/1", headers=h).status_code == 200      # hết ràng buộc
