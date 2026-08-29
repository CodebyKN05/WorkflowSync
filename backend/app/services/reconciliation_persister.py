import uuid
from dataclasses import dataclass
from typing import List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.reconciliation_run import ReconciliationRun
from app.models.match import Match
from app.services.confidence_scorer import ConfidenceScoreResult
from app.services.result_classifier import ClassificationResult, ResultCategory
from app.services.explainability_service import ExplanationResult

@dataclass
class MatchData:
    invoice_id: uuid.UUID
    transaction_id: uuid.UUID
    confidence_result: ConfidenceScoreResult
    classification_result: ClassificationResult
    explanation_result: ExplanationResult


def persist_reconciliation_run(
    db: Session,
    client_id: uuid.UUID,
    match_results: List[MatchData],
    unmatched_invoice_count: int = 0
) -> ReconciliationRun:
    """
    Persists a new reconciliation run and its associated matches.
    Keeps historical runs untouched.
    Filters out intra-run duplicates for the same candidate pair.
    """
    
    # Dedup MatchData by candidate pair identity (invoice_id, transaction_id)
    seen_pairs = set()
    unique_matches = []
    
    for match in match_results:
        pair_identity = (match.invoice_id, match.transaction_id)
        if pair_identity not in seen_pairs:
            seen_pairs.add(pair_identity)
            unique_matches.append(match)

    matched_count = 0
    review_count = 0
    unmatched_count = unmatched_invoice_count
    duplicate_count = 0

    # Categorize counts based on classification result
    for match in unique_matches:
        if match.classification_result.category == ResultCategory.MATCHED:
            matched_count += 1
        elif match.classification_result.category == ResultCategory.NEEDS_REVIEW:
            review_count += 1
        elif match.classification_result.category == ResultCategory.UNMATCHED:
            unmatched_count += 1
        elif match.classification_result.category == ResultCategory.DUPLICATE:
            duplicate_count += 1

    run = ReconciliationRun(
        client_id=client_id,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        matched_count=matched_count,
        review_count=review_count,
        unmatched_count=unmatched_count,
        duplicate_count=duplicate_count,
        status="completed"
    )

    try:
        db.add(run)
        db.flush()
        
        db_matches = []
        for match_data in unique_matches:
            db_match = Match(
                reconciliation_run_id=run.id,
                invoice_id=match_data.invoice_id,
                transaction_id=match_data.transaction_id,
                score=match_data.confidence_result.total_score,
                status=match_data.classification_result.category.value,
                reason="\n".join(match_data.explanation_result.reasons)
            )
            db_matches.append(db_match)

        db.add_all(db_matches)
        db.commit()
        db.refresh(run)
    except Exception as e:
        db.rollback()
        raise e

    return run
