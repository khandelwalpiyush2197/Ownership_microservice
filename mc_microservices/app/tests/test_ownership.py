from fastapi.testclient import TestClient
from mc_microservices.main import app

client = TestClient(app)

def test_claim_ownership():
    response = client.post("/ownership/claim_ownership", json={
        "eid_list": [1, 2, 3],
        "group_name": "test",
        "PG_size": "small",
        "WB_type": "premium",
        "env": "dev",
        "number_of_days": 5,
        "namespace": "default",
        "role_name": "test-role"
    })
    assert response.status_code == 200
    assert "pg_id" in response.json()
    assert "auth_token" in response.json()

def test_relinquish_ownership():
    response = client.post("/ownership/claim_ownership", json={
        "eid_list": [1, 2, 3],
        "group_name": "test",
        "PG_size": "small",
        "WB_type": "premium",
        "env": "dev",
        "number_of_days": 5,
        "namespace": "default",
        "role_name": "test-role"
    })
    pg_id = response.json()["pg_id"]
    response = client.delete(f"/ownership/relinquish_ownership", params={"pg_id": pg_id})
    assert response.status_code == 200
    assert response.json() == {"message": "Ownership relinquished"}

def test_validate_ownership():
    response = client.post("/ownership/claim_ownership", json={
        "eid_list": [1, 2, 3],
        "group_name": "test",
        "PG_size": "small",
        "WB_type": "premium",
        "env": "dev",
        "number_of_days": 5,
        "namespace": "default",
        "role_name": "test-role"
    })
    pg_id = response.json()["pg_id"]
    response = client.get(f"/ownership/validate_ownership", params={"pg_id": pg_id})
    assert response.status_code == 200
    assert response.json() == {"is_valid": True}