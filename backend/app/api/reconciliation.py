import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.match import Match
from app.models.reconciliation_run import ReconciliationRun
from app.models.client import Client
from app.schemas.reconciliation import ReviewCandidateResponse

router = APIRouter()

@router.get("/runs/{run_id}/queue", response_model=List[ReviewCandidateResponse])
def get_review_queue(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the manual resolution review queue for a specific reconciliation run.
    Only returns candidates classified as NEEDS_REVIEW or DUPLICATE.
    """
    # 1. Fetch the run and ensure it exists
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reconciliation run not found"
        )
        
    # 2. Enforce client isolation
    client = db.query(Client).filter(Client.id == run.client_id).first()
    if not client or client.firm_id != current_user.firm_id:  # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this run"
        )
        
    # 3. Query the matches with their related invoice and transaction
    matches = (
        db.query(Match)
        .filter(Match.reconciliation_run_id == run_id)
        .filter(Match.status.in_(["NEEDS_REVIEW", "DUPLICATE"]))
        .all()
    )
    
    return matches
