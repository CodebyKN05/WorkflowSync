from app.services.result_classifier import classify_result, ResultCategory

def test_matched_upper_boundary():
    result = classify_result(confidence_score=100.0, is_duplicate=False)
    assert result.category == ResultCategory.MATCHED

def test_matched_lower_boundary():
    result = classify_result(confidence_score=85.0, is_duplicate=False)
    assert result.category == ResultCategory.MATCHED

def test_needs_review_upper_boundary():
    result = classify_result(confidence_score=84.99, is_duplicate=False)
    assert result.category == ResultCategory.NEEDS_REVIEW

def test_needs_review_lower_boundary():
    result = classify_result(confidence_score=60.0, is_duplicate=False)
    assert result.category == ResultCategory.NEEDS_REVIEW

def test_unmatched_upper_boundary():
    result = classify_result(confidence_score=59.99, is_duplicate=False)
    assert result.category == ResultCategory.UNMATCHED

def test_unmatched_lower_boundary():
    result = classify_result(confidence_score=0.0, is_duplicate=False)
    assert result.category == ResultCategory.UNMATCHED

def test_duplicate_overrides_score():
    # If is_duplicate is True, the score is ignored
    assert classify_result(confidence_score=100.0, is_duplicate=True).category == ResultCategory.DUPLICATE
    assert classify_result(confidence_score=85.0, is_duplicate=True).category == ResultCategory.DUPLICATE
    assert classify_result(confidence_score=60.0, is_duplicate=True).category == ResultCategory.DUPLICATE
    assert classify_result(confidence_score=0.0, is_duplicate=True).category == ResultCategory.DUPLICATE
