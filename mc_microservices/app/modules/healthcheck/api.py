from fastapi import APIRouter, HTTPException
import requests

router = APIRouter()

@router.get("/healthcheck", tags=["Health Check"])
async def healthcheck():
    health_status = {
        "ownership_claim": False,
        "ownership_relinquish": False,
        "ownership_validate": False
    }

    try:
        # Check ownership claim endpoint
        response = requests.post("http://localhost:8000/ownership/claim_ownership", json={
            "eid_list": [1, 2, 3],
            "group_name": "test",
            "PG_size": "small"
        })
        if response.status_code == 200:
            health_status["ownership_claim"] = True
    except Exception as e:
        print(f"Error checking ownership claim: {e}")

    try:
        # Check ownership relinquish endpoint
        response = requests.delete("http://localhost:8000/relinquish/relinquish_ownership", params={"pg_id": "test_pg_id", "eid": "test_eid"})
        if response.status_code == 200:
            health_status["ownership_relinquish"] = True
    except Exception as e:
        print(f"Error checking ownership relinquish: {e}")

    try:
        # Check ownership validate endpoint
        response = requests.post("http://localhost:8000/validate/validate-ownership", json={"eid": "test_eid", "auth_token": "test_token"})
        if response.status_code == 200:
            health_status["ownership_validate"] = True
    except Exception as e:
        print(f"Error checking ownership validate: {e}")

    return health_status