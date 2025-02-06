from fastapi.testclient import TestClient
from mc_microservices.main import app

client = TestClient(app)

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
    response = client.get(f"/validate/validate_ownership", params={"pg_id": pg_id})
    assert response.status_code == 200
    assert response.json() == {"is_valid": True}