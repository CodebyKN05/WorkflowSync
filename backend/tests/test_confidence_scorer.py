from decimal import Decimal
from app.services.amount_comparator import AmountComparisonResult
from app.services.vendor_comparator import VendorComparisonResult
from app.services.date_comparator import DateComparisonResult
from app.services.reference_comparator import ReferenceComparisonResult
from app.services.confidence_scorer import calculate_confidence_score

def test_all_signals_matching_yields_100():
    result = calculate_confidence_score(
        AmountComparisonResult(is_exact_match=True, difference=Decimal("0")),
        VendorComparisonResult(similarity_score=100.0),
        DateComparisonResult(is_exact_match=True, days_difference=0),
        ReferenceComparisonResult(is_exact_match=True)
    )
    assert result.total_score == 100.0

def test_amount_only_yields_40():
    result = calculate_confidence_score(
        AmountComparisonResult(is_exact_match=True, difference=Decimal("0")),
        VendorComparisonResult(similarity_score=0.0),
        DateComparisonResult(is_exact_match=False, days_difference=5),
        ReferenceComparisonResult(is_exact_match=False)
    )
    assert result.total_score == 40.0

def test_vendor_only_yields_proportional_score():
    result = calculate_confidence_score(
        AmountComparisonResult(is_exact_match=False, difference=Decimal("100")),
        VendorComparisonResult(similarity_score=85.0),
        DateComparisonResult(is_exact_match=False, days_difference=5),
        ReferenceComparisonResult(is_exact_match=False)
    )
    assert result.total_score == 25.5

def test_date_only_yields_15():
    result = calculate_confidence_score(
        AmountComparisonResult(is_exact_match=False, difference=Decimal("100")),
        VendorComparisonResult(similarity_score=0.0),
        DateComparisonResult(is_exact_match=True, days_difference=0),
        ReferenceComparisonResult(is_exact_match=False)
    )
    assert result.total_score == 15.0

def test_reference_only_yields_15():
    result = calculate_confidence_score(
        AmountComparisonResult(is_exact_match=False, difference=Decimal("100")),
        VendorComparisonResult(similarity_score=0.0),
        DateComparisonResult(is_exact_match=False, days_difference=5),
        ReferenceComparisonResult(is_exact_match=True)
    )
    assert result.total_score == 15.0

def test_no_signals_yields_0():
    result = calculate_confidence_score(
        AmountComparisonResult(is_exact_match=False, difference=Decimal("100")),
        VendorComparisonResult(similarity_score=0.0),
        DateComparisonResult(is_exact_match=False, days_difference=5),
        ReferenceComparisonResult(is_exact_match=False)
    )
    assert result.total_score == 0.0

def test_combined_scores():
    result = calculate_confidence_score(
        AmountComparisonResult(is_exact_match=True, difference=Decimal("0")),
        VendorComparisonResult(similarity_score=50.0),
        DateComparisonResult(is_exact_match=False, days_difference=5),
        ReferenceComparisonResult(is_exact_match=True)
    )
    # 40 (amount) + 15 (vendor) + 15 (reference) = 70.0
    assert result.total_score == 70.0

def test_deterministic_repeated_calls():
    for _ in range(5):
        result = calculate_confidence_score(
            AmountComparisonResult(is_exact_match=True, difference=Decimal("0")),
            VendorComparisonResult(similarity_score=85.0),
            DateComparisonResult(is_exact_match=True, days_difference=0),
            ReferenceComparisonResult(is_exact_match=True)
        )
        assert result.total_score == 40.0 + 25.5 + 15.0 + 15.0
