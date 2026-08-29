from datetime import date
from decimal import Decimal
import pytest
from app.schemas.transaction import TransactionParsedRow
from app.services.transaction_normalizer import normalize_transactions
from app.core.exceptions import AppException

def test_normalize_valid_iso_date():
    rows = [TransactionParsedRow(transaction_date="2023-10-01", description="Test", amount="100.00", currency="USD")]
    normalized = normalize_transactions(rows)
    assert normalized[0].transaction_date == date(2023, 10, 1)

def test_normalize_supported_alternate_date_formats():
    rows = [
        TransactionParsedRow(transaction_date="10/25/2023", description="Test", amount="100.00", currency="USD"), # MM/DD/YYYY unambiguously
        TransactionParsedRow(transaction_date="25/10/2023", description="Test", amount="100.00", currency="USD")  # DD/MM/YYYY unambiguously
    ]
    normalized = normalize_transactions(rows)
    assert normalized[0].transaction_date == date(2023, 10, 25)
    assert normalized[1].transaction_date == date(2023, 10, 25)

def test_normalize_ambiguous_invalid_date_handling():
    # Ambiguous date like 05/06/2023 (May 6th or Jun 5th)
    rows = [TransactionParsedRow(transaction_date="05/06/2023", description="Test", amount="100.00", currency="USD")]
    with pytest.raises(AppException) as excinfo:
        normalize_transactions(rows)
    assert "Ambiguous date format: 05/06/2023" in excinfo.value.detail

    # Invalid date
    rows = [TransactionParsedRow(transaction_date="InvalidDate", description="Test", amount="100.00", currency="USD")]
    with pytest.raises(AppException) as excinfo:
        normalize_transactions(rows)
    assert "Invalid date format: InvalidDate" in excinfo.value.detail

def test_normalize_amount_conversion_to_decimal():
    rows = [TransactionParsedRow(transaction_date="2023-10-01", description="Test", amount="-150.50", currency="USD")]
    normalized = normalize_transactions(rows)
    assert normalized[0].amount == Decimal("-150.50")

def test_normalize_comma_formatted_amounts():
    rows = [TransactionParsedRow(transaction_date="2023-10-01", description="Test", amount="1,234,567.89", currency="USD")]
    normalized = normalize_transactions(rows)
    assert normalized[0].amount == Decimal("1234567.89")

def test_normalize_currency_symbol_handling():
    rows = [
        TransactionParsedRow(transaction_date="2023-10-01", description="Test", amount="$1000.00", currency="USD"),
        TransactionParsedRow(transaction_date="2023-10-02", description="Test", amount="€2,000.00", currency="EUR")
    ]
    normalized = normalize_transactions(rows)
    assert normalized[0].amount == Decimal("1000.00")
    assert normalized[1].amount == Decimal("2000.00")

def test_normalize_currency_uppercase():
    rows = [TransactionParsedRow(transaction_date="2023-10-01", description="Test", amount="100.00", currency=" inr ")]
    normalized = normalize_transactions(rows)
    assert normalized[0].currency == "INR"

def test_normalize_description_whitespace_trimming():
    rows = [TransactionParsedRow(transaction_date="2023-10-01", description="  Test Vendor  \n", amount="100.00", currency="USD")]
    normalized = normalize_transactions(rows)
    assert normalized[0].description == "Test Vendor"

def test_normalize_reference_whitespace_trimming():
    rows = [TransactionParsedRow(transaction_date="2023-10-01", description="Test", amount="100.00", currency="USD", reference="  REF-99  ")]
    normalized = normalize_transactions(rows)
    assert normalized[0].reference == "REF-99"

def test_normalize_missing_optional_reference_remains_none():
    rows = [TransactionParsedRow(transaction_date="2023-10-01", description="Test", amount="100.00", currency="USD", reference="   ")]
    normalized = normalize_transactions(rows)
    assert normalized[0].reference is None

def test_normalize_multiple_rows():
    rows = [
        TransactionParsedRow(transaction_date="2023-10-01", description="Test 1", amount="10.00", currency="USD"),
        TransactionParsedRow(transaction_date="2023-10-02", description="Test 2", amount="20.00", currency="USD")
    ]
    normalized = normalize_transactions(rows)
    assert len(normalized) == 2
    assert normalized[0].description == "Test 1"
    assert normalized[1].description == "Test 2"

def test_invalid_normalization_produces_clear_error():
    rows = [
        TransactionParsedRow(transaction_date="2023-10-01", description="Test 1", amount="10.00", currency="USD"),
        TransactionParsedRow(transaction_date="2023-10-02", description="Test 2", amount="NotAnAmount", currency="USD"),
        TransactionParsedRow(transaction_date="2023-10-03", description="Test 3", amount="30.00", currency="TOO_LONG")
    ]
    with pytest.raises(AppException) as excinfo:
        normalize_transactions(rows)
    
    assert "Normalization failed for 2 row(s)" in excinfo.value.detail
    assert "Row 2: Invalid amount format: NotAnAmount" in excinfo.value.detail
    assert "Row 3: Invalid currency format: TOO_LONG" in excinfo.value.detail
