from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.modules.validate.schema import ValidateOwnershipRequest, OwnershipValidationResponse
from .utils import get_token_from_vault
from app.modules.ownership.utils.logger import logger

router = APIRouter()

@router.post("/validate-ownership", response_model=OwnershipValidationResponse)
async def validate_ownership(request: ValidateOwnershipRequest):
    logger.debug(f"Received request to validate ownership for eid: {request.eid}")
    # Retrieve the stored token for the provided eid from Vault
    stored_token = get_token_from_vault(request.eid)

    if stored_token is None:
        # If no token is found for the given eid, inform the user that ownership is invalid
        logger.info(f"No token found for eid {request.eid}")
        return JSONResponse(
            status_code=404,
            content={"is_valid": False, "message": f"No token found for eid {request.eid}. Invalid ownership."}
        )

    # Compare the provided auth_token with the stored token
    if request.auth_token == stored_token:
        logger.info(f"Token validated successfully for eid {request.eid}")
        return {"is_valid": True, "message": "Good token. Valid ownership."}
    else:
        logger.info(f"Invalid token provided for eid {request.eid}")
        return {"is_valid": False, "message": "Bad token. Invalid ownership."}