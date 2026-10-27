def test_vaccination_crud_and_permissions(client, auth):
    admin = auth('admin')
    body = {'pet_id': 1, 'vaccine_name': 'Dại', 'last_date': None, 'next_due_date': '2027-03-01', 'status': 'PENDING'}
    r = client.post('/api/vaccinations', json=body, headers=admin)
    assert r.status_code == 201, r.text
    rid = r.json()['reminder_id']
    body.update(vaccine_name='Nhắc dại', status='DONE')
    r = client.put(f'/api/vaccinations/{rid}', json=body, headers=admin)
    assert r.status_code == 200 and r.json()['vaccine_name'] == 'Nhắc dại' and r.json()['status'] == 'DONE'
    assert client.delete(f'/api/vaccinations/{rid}', headers=auth('groomer')).status_code == 403
    assert client.delete(f'/api/vaccinations/{rid}', headers=admin).status_code == 200
    assert not any(v['reminder_id'] == rid for v in client.get('/api/vaccinations', headers=admin).json())


def test_pet_owner_change(client, auth):
    admin = auth('admin')
    r = client.post('/api/owners', json={'full_name': 'Chủ mới', 'phone': '0123456789'}, headers=admin)
    assert r.status_code == 201
    owner_id = r.json()['owner_id']
    r = client.put('/api/pets/1', json={'owner_id': owner_id, 'age': 0}, headers=admin)
    assert r.status_code == 200 and r.json()['owner_id'] == owner_id and r.json()['age'] == 0
    assert client.put('/api/pets/1', json={'owner_id': 9999}, headers=admin).status_code == 404
