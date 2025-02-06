import requests
from fastapi import HTTPException
from app.modules.ownership.utils.logger import logger

def validate_token(pg_id: str, auth_token: str) -> bool:
    """
    Validates the authorization token using the validate API.

    Args:
        pg_id (str): The playground ID.
        auth_token (str): The authorization token.

    Returns:
        bool: True if the token is valid, False otherwise.
    """
    try:
        response = requests.post(
            "http://localhost:8000/validate/validate-ownership",
            json={"pg_id": pg_id, "auth_token": auth_token}
        )
        if response.status_code == 200 and response.json().get("is_valid"):
            return True
        return False
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")