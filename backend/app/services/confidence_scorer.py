from dataclasses import dataclass
from app.services.amount_comparator import AmountComparisonResult
from app.services.vendor_comparator import VendorComparisonResult
from app.services.date_comparator import DateComparisonResult
from app.services.reference_comparator import ReferenceComparisonResult

@dataclass
class ConfidenceScoreResult:
    """
    Represents the calculated confidence score of a candidate match.
    """
    total_score: float

def calculate_confidence_score(
    amount_result: AmountComparisonResult,
    vendor_result: VendorComparisonResult,
    date_result: DateComparisonResult,
    reference_result: ReferenceComparisonResult
) -> ConfidenceScoreResult:
    """
    Calculates the numerical confidence score based on the raw comparison facts.
    
    Maximum score: 100 points.
    - Amount: +40 (exact match only)
    - Vendor: +30 (proportional to similarity percentage)
    - Date: +15 (exact match only)
    - Reference: +15 (exact match only)
    """
    score = 0.0
    
    if amount_result.is_exact_match:
        score += 40.0
        
    score += (30.0 * vendor_result.similarity_score / 100.0)
    
    if date_result.is_exact_match:
        score += 15.0
        
    if reference_result.is_exact_match:
        score += 15.0
        
    return ConfidenceScoreResult(total_score=score)
