from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.firm import Firm
from app.schemas.firm import FirmResponse

router = APIRouter()

@router.get("/me", response_model=FirmResponse)
def get_my_firm(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    firm = db.query(Firm).filter(Firm.id == current_user.firm_id).first()
    if not firm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Firm not found")
    return firm
