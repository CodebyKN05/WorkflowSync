from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

class ClientResponse(BaseModel):
    id: uuid.UUID
    firm_id: uuid.UUID
    name: str
    industry: Optional[str] = None
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}
