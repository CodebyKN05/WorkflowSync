from pydantic import BaseModel
import uuid
from datetime import datetime

class FirmResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
