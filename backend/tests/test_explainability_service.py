from decimal import Decimal
from app.services.amount_comparator import AmountComparisonResult
from app.services.vendor_comparator import VendorComparisonResult
from app.services.date_comparator import DateComparisonResult
from app.services.reference_comparator import ReferenceComparisonResult
from app.services.confidence_scorer import ConfidenceScoreResult
from app.services.result_classifier import ClassificationResult, ResultCategory
from app.services.explainability_service import generate_explanation

def test_perfect_match_explanation():
    explanation = generate_explanation(
        amount_result=AmountComparisonResult(is_exact_match=True, difference=Decimal("0")),
        vendor_result=VendorComparisonResult(similarity_score=100.0),
        date_result=DateComparisonResult(is_exact_match=True, days_difference=0),
        reference_result=ReferenceComparisonResult(is_exact_match=True),
        classification_result=ClassificationResult(category=ResultCategory.MATCHED),
        confidence_result=ConfidenceScoreResult(total_score=100.0)
    )
    
    assert explanation.reasons == [
        "Amount: Exact match",
        "Vendor: 100.0% similar",
        "Date: Exact match",
        "Reference: Found",
        "Result: MATCHED",
        "Confidence: 100.0"
    ]

def test_imperfect_match_explanation():
    explanation = generate_explanation(
        amount_result=AmountComparisonResult(is_exact_match=False, difference=Decimal("12.50")),
        vendor_result=VendorComparisonResult(similarity_score=85.0),
        date_result=DateComparisonResult(is_exact_match=False, days_difference=3),
        reference_result=ReferenceComparisonResult(is_exact_match=False),
        classification_result=ClassificationResult(category=ResultCategory.NEEDS_REVIEW),
        confidence_result=ConfidenceScoreResult(total_score=60.0)
    )
    
    assert explanation.reasons == [
        "Amount: 12.50 difference",
        "Vendor: 85.0% similar",
        "Date: 3 days apart",
        "Reference: Not found",
        "Result: NEEDS_REVIEW",
        "Confidence: 60.0"
    ]

def test_duplicate_explanation():
    explanation = generate_explanation(
        amount_result=AmountComparisonResult(is_exact_match=True, difference=Decimal("0")),
        vendor_result=VendorComparisonResult(similarity_score=100.0),
        date_result=DateComparisonResult(is_exact_match=True, days_difference=0),
        reference_result=ReferenceComparisonResult(is_exact_match=True),
        classification_result=ClassificationResult(category=ResultCategory.DUPLICATE),
        confidence_result=ConfidenceScoreResult(total_score=100.0)
    )
    
    assert explanation.reasons == [
        "Amount: Exact match",
        "Vendor: 100.0% similar",
        "Date: Exact match",
        "Reference: Found",
        "Result: Duplicate candidate",
        "Confidence: 100.0"
    ]
