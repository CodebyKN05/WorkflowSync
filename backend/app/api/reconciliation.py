import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.match import Match
from app.models.reconciliation_run import ReconciliationRun
from app.models.client import Client
from app.schemas.reconciliation import ReviewCandidateResponse, ResolveRequest, ReconciliationRunResponse, ReconciliationRunSummaryResponse

router = APIRouter()

@router.get("/runs", response_model=List[ReconciliationRunResponse])
def get_reconciliation_runs(
    client_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves persisted reconciliation run records.
    Filters to only runs belonging to the user's firm.
    Optionally filters by a specific client.
    """
    query = db.query(ReconciliationRun).join(Client)
    query = query.filter(Client.firm_id == current_user.firm_id)
    
    if client_id:
        query = query.filter(ReconciliationRun.client_id == client_id)
        
    runs = query.order_by(ReconciliationRun.started_at.desc()).all()
    return runs



@router.get("/runs/{run_id}/summary", response_model=ReconciliationRunSummaryResponse)
def get_reconciliation_run_summary(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the summary metrics of a specific reconciliation run.
    """
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reconciliation run not found"
        )

    # Enforce client isolation
    client = db.query(Client).filter(Client.id == run.client_id).first()
    if not client or client.firm_id != current_user.firm_id:  # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reconciliation run not found"
        )

    return run


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
    if match.status == "MATCHED":  # pyright: ignore[reportGeneralTypeIssues]
        return match

    # 4. Atomic update of Match and ReconciliationRun
    previous_status = match.status
    match.status = "MATCHED"  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
    match.updated_at = datetime.now(timezone.utc)  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

    # We must lock the run record to avoid race conditions when updating counts
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == match.reconciliation_run_id).with_for_update().first()
    if run:
        run.matched_count += 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
        if previous_status == "NEEDS_REVIEW":  # pyright: ignore[reportGeneralTypeIssues]
            run.review_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
        elif previous_status == "DUPLICATE":  # pyright: ignore[reportGeneralTypeIssues]
            run.duplicate_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
        elif previous_status == "UNMATCHED":  # pyright: ignore[reportGeneralTypeIssues]
            run.unmatched_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

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
    if match.status == "UNMATCHED":  # pyright: ignore[reportGeneralTypeIssues]
        return match
    if match.status == "MATCHED":  # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot reject a confirmed match"
        )

    # 4. Atomic update of Match and ReconciliationRun
    previous_status = match.status
    match.status = "UNMATCHED"  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
    match.updated_at = datetime.now(timezone.utc)  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

    # Lock the run record
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == match.reconciliation_run_id).with_for_update().first()
    if run:
        if previous_status == "NEEDS_REVIEW":  # pyright: ignore[reportGeneralTypeIssues]
            run.review_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
        elif previous_status == "DUPLICATE":  # pyright: ignore[reportGeneralTypeIssues]
            run.duplicate_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

        # Check if invoice is fully unmatched (no other viable candidates)
        # Viable candidates are those in NEEDS_REVIEW, DUPLICATE, or MATCHED
        other_candidates = db.query(Match).filter(
            Match.reconciliation_run_id == run.id,
            Match.invoice_id == match.invoice_id,
            Match.id != match.id,
            Match.status.in_(["NEEDS_REVIEW", "DUPLICATE", "MATCHED"])
        ).count()

        if other_candidates == 0:
            run.unmatched_count += 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

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

@router.post("/invoices/{invoice_id}/resolve", response_model=ReviewCandidateResponse)
def resolve_invoice(
    invoice_id: uuid.UUID,
    request: ResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resolves an invoice by selecting one of its existing candidate transactions.
    The selected candidate becomes MATCHED, while all sibling candidates become UNMATCHED.
    """
    # 1. Fetch all existing candidates for this invoice
    matches = db.query(Match).filter(Match.invoice_id == invoice_id).all()
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or has no candidate matches"
        )

    # 2. Enforce firm isolation
    invoice = matches[0].invoice
    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    if not client or client.firm_id != current_user.firm_id:  # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this invoice"
        )

    # 3. Ensure the supplied transaction is an existing candidate
    target_match = next((m for m in matches if m.transaction_id == request.transaction_id), None)  # pyright: ignore[reportGeneralTypeIssues]
    if not target_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate transaction not found for this invoice"
        )

    # 4. Enforce client isolation for the transaction (safety check)
    if target_match.transaction.client_id != invoice.client_id:  # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Transaction does not belong to the same client"
        )

    # 5. Handle idempotency
    if target_match.status == "MATCHED":  # pyright: ignore[reportGeneralTypeIssues]
        return target_match

    # 6. Atomic update of Matches and ReconciliationRun
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == target_match.reconciliation_run_id).with_for_update().first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reconciliation run not found"
        )

    # Check if invoice had no viable matches BEFORE
    viable_before = sum(1 for m in matches if m.status in ["NEEDS_REVIEW", "DUPLICATE", "MATCHED"])
    was_unmatched = (viable_before == 0)

    # Process target match
    previous_target_status = target_match.status
    target_match.status = "MATCHED"  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
    target_match.updated_at = datetime.now(timezone.utc)  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

    run.matched_count += 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
    if previous_target_status == "NEEDS_REVIEW":  # pyright: ignore[reportGeneralTypeIssues]
        run.review_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
    elif previous_target_status == "DUPLICATE":  # pyright: ignore[reportGeneralTypeIssues]
        run.duplicate_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

    # Process all sibling matches
    for m in matches:
        if m.id != target_match.id and m.status != "UNMATCHED":  # pyright: ignore[reportGeneralTypeIssues]
            prev_status = m.status
            m.status = "UNMATCHED"  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
            m.updated_at = datetime.now(timezone.utc)  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

            if prev_status == "NEEDS_REVIEW":  # pyright: ignore[reportGeneralTypeIssues]
                run.review_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
            elif prev_status == "DUPLICATE":  # pyright: ignore[reportGeneralTypeIssues]
                run.duplicate_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]
            elif prev_status == "MATCHED":  # pyright: ignore[reportGeneralTypeIssues]
                run.matched_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

    if was_unmatched:
        run.unmatched_count -= 1  # pyright: ignore[reportAttributeAccessIssue, reportGeneralTypeIssues]

    try:
        db.commit()
        db.refresh(target_match)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve invoice"
        )

    return target_match
