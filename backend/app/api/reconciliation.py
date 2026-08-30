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

from datetime import datetime, timezone

@router.post("/matches/{match_id}/confirm", response_model=ReviewCandidateResponse)
def confirm_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Confirms a candidate match, transitioning it to MATCHED status.
    Idempotent if the match is already MATCHED.
    Adjusts the parent ReconciliationRun counts atomically.
    """
    # 1. Fetch match with related entities
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
        
    # 2. Enforce client isolation
    invoice = match.invoice
    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    if not client or client.firm_id != current_user.firm_id:  # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this match"
        )
        
    # 3. Handle idempotency
    if match.status == "MATCHED":
        return match
        
    # 4. Atomic update of Match and ReconciliationRun
    previous_status = match.status
    match.status = "MATCHED"
    match.updated_at = datetime.now(timezone.utc)
    
    # We must lock the run record to avoid race conditions when updating counts
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == match.reconciliation_run_id).with_for_update().first()
    if run:
        run.matched_count += 1
        if previous_status == "NEEDS_REVIEW":
            run.review_count -= 1
        elif previous_status == "DUPLICATE":
            run.duplicate_count -= 1
        elif previous_status == "UNMATCHED":
            run.unmatched_count -= 1
            
    try:
        db.commit()
        db.refresh(match)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm match"
        )
    
    return match

@router.post("/matches/{match_id}/reject", response_model=ReviewCandidateResponse)
def reject_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rejects a candidate match, transitioning it to UNMATCHED status.
    Idempotent if already UNMATCHED.
    Returns a conflict if already MATCHED.
    Adjusts the parent ReconciliationRun counts atomically.
    """
    # 1. Fetch match with related entities
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # 2. Enforce client isolation
    invoice = match.invoice
    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    if not client or client.firm_id != current_user.firm_id:  # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this match"
        )

    # 3. Handle idempotency and conflict
    if match.status == "UNMATCHED":
        return match
    if match.status == "MATCHED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot reject a confirmed match"
        )

    # 4. Atomic update of Match and ReconciliationRun
    previous_status = match.status
    match.status = "UNMATCHED"
    match.updated_at = datetime.now(timezone.utc)

    # Lock the run record
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == match.reconciliation_run_id).with_for_update().first()
    if run:
        if previous_status == "NEEDS_REVIEW":
            run.review_count -= 1
        elif previous_status == "DUPLICATE":
            run.duplicate_count -= 1

        # Check if invoice is fully unmatched (no other viable candidates)
        # Viable candidates are those in NEEDS_REVIEW, DUPLICATE, or MATCHED
        other_candidates = db.query(Match).filter(
            Match.reconciliation_run_id == run.id,
            Match.invoice_id == match.invoice_id,
            Match.id != match.id,
            Match.status.in_(["NEEDS_REVIEW", "DUPLICATE", "MATCHED"])
        ).count()

        if other_candidates == 0:
            run.unmatched_count += 1

    try:
        db.commit()
        db.refresh(match)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject match"
        )

    return match
