from pydantic import BaseModel
from typing import List

class ClaimOwnershipRequest(BaseModel):
    eid_list: List[str]
    num_days: int
    size: str
    environment: str
    wb_bech_type: str
    # group_name: str