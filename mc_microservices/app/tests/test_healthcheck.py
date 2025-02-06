from fastapi.testclient import TestClient
from mc_microservices.main import app

client = TestClient(app)

def test_ownership_claim():
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

def test_ownership_relinquish():
    response = client.delete("/ownership/relinquish_ownership", params={"pg_id": "test_pg_id"})
    assert response.status_code == 200

def test_ownership_validate():
    response = client.get("/ownership/validate_ownership", params={"pg_id": "test_pg_id"})
    assert response.status_code == 200