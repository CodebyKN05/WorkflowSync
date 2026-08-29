from dataclasses import dataclass
from typing import List

from app.services.amount_comparator import AmountComparisonResult
from app.services.vendor_comparator import VendorComparisonResult
from app.services.date_comparator import DateComparisonResult
from app.services.reference_comparator import ReferenceComparisonResult
from app.services.confidence_scorer import ConfidenceScoreResult
from app.services.result_classifier import ClassificationResult, ResultCategory

@dataclass
class ExplanationResult:
    """
    Contains deterministic, human-readable explanations derived from the reconciliation facts.
    """
    reasons: List[str]

def generate_explanation(
    amount_result: AmountComparisonResult,
    vendor_result: VendorComparisonResult,
    date_result: DateComparisonResult,
    reference_result: ReferenceComparisonResult,
    classification_result: ClassificationResult,
    confidence_result: ConfidenceScoreResult
) -> ExplanationResult:
    """
    Generates an explanation for a candidate match based purely on provided facts.
    Does not recalculate any signals.
    """
    reasons = []

    if amount_result.is_exact_match:
        reasons.append("Amount: Exact match")
    else:
        reasons.append(f"Amount: {amount_result.difference} difference")

    reasons.append(f"Vendor: {vendor_result.similarity_score}% similar")

    if date_result.is_exact_match:
        reasons.append("Date: Exact match")
    else:
        reasons.append(f"Date: {date_result.days_difference} days apart")

    if reference_result.is_exact_match:
        reasons.append("Reference: Found")
    else:
        reasons.append("Reference: Not found")

    if classification_result.category == ResultCategory.DUPLICATE:
        reasons.append("Result: Duplicate candidate")
    else:
        reasons.append(f"Result: {classification_result.category.value}")

    reasons.append(f"Confidence: {confidence_result.total_score}")

    return ExplanationResult(reasons=reasons)
