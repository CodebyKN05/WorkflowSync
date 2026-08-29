import uuid
from typing import List, Dict, Set
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.transaction import Transaction
from app.models.reconciliation_run import ReconciliationRun

from app.services.candidate_generator import generate_candidates, CandidatePair
from app.services.amount_comparator import compare_amounts
from app.services.vendor_comparator import compare_vendors
from app.services.date_comparator import compare_dates
from app.services.reference_comparator import compare_references
from app.services.confidence_scorer import calculate_confidence_score
from app.services.result_classifier import classify_result, ClassificationResult, ResultCategory
from app.services.explainability_service import generate_explanation
from app.services.reconciliation_persister import persist_reconciliation_run, MatchData

def run_reconciliation(
    db: Session,
    client_id: uuid.UUID,
    invoices: List[Invoice],
    transactions: List[Transaction]
) -> ReconciliationRun:
    """
    Orchestrates the entire reconciliation pipeline for a given set of invoices and transactions.
    """
    
    match_data_list: List[MatchData] = []
    
    # 1. Generate candidates
    all_candidates = generate_candidates(invoices, transactions)
    
    # Track unmatched invoices
    invoices_with_candidates = {c.invoice.id for c in all_candidates}
    unmatched_invoice_count = len(invoices) - len(invoices_with_candidates)
    
    # Group candidates by invoice to identify duplicates
    invoice_candidates_map = {}
    for candidate in all_candidates:
        if candidate.invoice.id not in invoice_candidates_map:
            invoice_candidates_map[candidate.invoice.id] = []
        invoice_candidates_map[candidate.invoice.id].append(candidate)
        
    # Process candidates
    for invoice_id, candidates in invoice_candidates_map.items():
        is_duplicate = len(candidates) > 1
        
        for candidate in candidates:
            amount_result = compare_amounts(candidate.invoice.amount, candidate.transaction.amount) # type: ignore
            vendor_result = compare_vendors(candidate.invoice.vendor, candidate.transaction.description) # type: ignore
            date_result = compare_dates(candidate.invoice.invoice_date, candidate.transaction.transaction_date) # type: ignore
            reference_result = compare_references(candidate.invoice.invoice_number, candidate.transaction.reference) # type: ignore
            
            confidence_result = calculate_confidence_score(
                amount_result=amount_result,
                vendor_result=vendor_result,
                date_result=date_result,
                reference_result=reference_result
            )
            
            classification_result = classify_result(
                confidence_score=confidence_result.total_score,
                is_duplicate=is_duplicate
            )
            
            explanation_result = generate_explanation(
                amount_result=amount_result,
                vendor_result=vendor_result,
                date_result=date_result,
                reference_result=reference_result,
                classification_result=classification_result,
                confidence_result=confidence_result
            )
            
            match_data = MatchData(
                invoice_id=candidate.invoice.id, # type: ignore
                transaction_id=candidate.transaction.id, # type: ignore
                confidence_result=confidence_result,
                classification_result=classification_result,
                explanation_result=explanation_result
            )
            
            match_data_list.append(match_data)
            
    # Persist
    run = persist_reconciliation_run(
        db=db,
        client_id=client_id,
        match_results=match_data_list,
        unmatched_invoice_count=unmatched_invoice_count
    )
    
    return run
