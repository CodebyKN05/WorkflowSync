from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    firm_id: uuid.UUID

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    firm_id: uuid.UUID

    model_config = {"from_attributes": True}
