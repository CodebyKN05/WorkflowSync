from datetime import date
from app.services.date_comparator import compare_dates

def test_exact_same_dates():
    result = compare_dates(date(2023, 1, 15), date(2023, 1, 15))
    assert result.is_exact_match is True
    assert result.days_difference == 0

def test_different_dates():
    result = compare_dates(date(2023, 1, 15), date(2023, 1, 20))
    assert result.is_exact_match is False
    assert result.days_difference == 5

def test_one_day_difference():
    result_forward = compare_dates(date(2023, 1, 15), date(2023, 1, 16))
    assert result_forward.is_exact_match is False
    assert result_forward.days_difference == 1
    
    result_backward = compare_dates(date(2023, 1, 15), date(2023, 1, 14))
    assert result_backward.is_exact_match is False
    assert result_backward.days_difference == 1

def test_dates_separated_by_multiple_days_across_months():
    result = compare_dates(date(2023, 1, 31), date(2023, 2, 5))
    assert result.is_exact_match is False
    assert result.days_difference == 5

def test_dates_separated_by_multiple_days_across_years():
    result = compare_dates(date(2022, 12, 31), date(2023, 1, 1))
    assert result.is_exact_match is False
    assert result.days_difference == 1

def test_deterministic_repeated_calls():
    for _ in range(5):
        result = compare_dates(date(2023, 6, 1), date(2023, 6, 2))
        assert result.is_exact_match is False
        assert result.days_difference == 1

def test_no_database_dependency():
    # Calling the pure function with simple primitives verifies it requires no db session or ORM state
    result = compare_dates(date(2020, 1, 1), date(2020, 1, 1))
    assert result.is_exact_match is True
