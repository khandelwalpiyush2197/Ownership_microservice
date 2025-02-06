from pydantic import BaseModel

class TriggerSparkPipelineRequest(BaseModel):
    pg_id: str
    auth_token: str

class TriggerSparkPipelineResponse(BaseModel):
    status: str
    output: str