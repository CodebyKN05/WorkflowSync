from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.client import Client
from app.schemas.client import ClientResponse

router = APIRouter()

@router.get("/", response_model=List[ClientResponse])
def get_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only return clients belonging to the authenticated user's firm
    clients = db.query(Client).filter(Client.firm_id == current_user.firm_id).all()
    return clients
