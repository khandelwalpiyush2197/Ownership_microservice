from pydantic import BaseModel

class ValidateOwnershipRequest(BaseModel):
    eid: str
    auth_token: str

class OwnershipValidationResponse(BaseModel):
    is_valid: bool
    message: str