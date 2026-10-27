"""Phân quyền được kiểm tra tại API, kể cả khi gọi trực tiếp không qua giao diện."""
import pytest


@pytest.mark.parametrize('method,path,body', [
    ('get', '/api/invoices', None),
    ('get', '/api/invoices/1', None),
    ('get', '/api/analytics/dashboard', None),
    ('get', '/api/analytics/services', None),
    ('get', '/api/analytics/revenue', None),
    ('post', '/api/appointments', {'pet_id': 1, 'service_id': 1, 'groomer_name': 'A', 'appointment_date': '2099-01-01', 'start_time': '09:00', 'end_time': '10:00'}),
    ('put', '/api/appointments/1', {'start_time': '10:00'}),
    ('delete', '/api/appointments/1', None),
    ('post', '/api/owners', {'full_name': 'Khách', 'phone': '01234'}),
    ('post', '/api/pets', {'owner_id': 1, 'pet_name': 'Bé', 'pet_type': 'CHO', 'weight': 3}),
    ('post', '/api/services', {'service_name': 'Tắm', 'duration_minutes': 30, 'price': 100}),
    ('post', '/api/vaccinations', {'pet_id': 1, 'vaccine_name': 'Dại', 'next_due_date': '2099-01-01'}),
    ('delete', '/api/care-records/1', None),
])
def test_groomer_cannot_access_restricted_operations(client, auth, method, path, body):
    response = client.request(method, path, headers=auth('groomer'), json=body)
    assert response.status_code == 403, (path, response.text)


@pytest.mark.parametrize('method,path,body', [
    ('post', '/api/services', {'service_name': 'Tắm', 'duration_minutes': 30, 'price': 100}),
    ('delete', '/api/pets/1', None),
    ('delete', '/api/owners/1', None),
    ('delete', '/api/care-records/1', None),
    ('delete', '/api/vaccinations/1', None),
    ('post', '/api/invoices/1/cancel', None),
    ('get', '/api/ai/logs', None),
])
def test_receptionist_cannot_access_admin_operations(client, auth, method, path, body):
    response = client.request(method, path, headers=auth('letan'), json=body)
    assert response.status_code == 403, (path, response.text)


def test_role_allowed_operations_and_anonymous_access(client, auth):
    groomer, receptionist, admin = (auth(role) for role in ('groomer', 'letan', 'admin'))
    assert client.get('/api/appointments', headers=groomer).status_code == 200
    assert client.get('/api/services', headers=groomer).status_code == 200
    assert client.post('/api/care-records', headers=groomer, json={'pet_id': 1, 'skin_condition': 'Bình thường'}).status_code == 201
    assert client.post('/api/ai/ask', headers=groomer, json={'question': 'Bao lâu tắm một lần?'}).status_code == 200
    assert client.get('/api/invoices', headers=receptionist).status_code == 200
    assert client.get('/api/analytics/dashboard', headers=receptionist).status_code == 200
    assert client.post('/api/services', headers=admin, json={'service_name': 'Tắm mới', 'duration_minutes': 30, 'price': 100}).status_code == 201
    assert client.get('/api/invoices').status_code == 401
