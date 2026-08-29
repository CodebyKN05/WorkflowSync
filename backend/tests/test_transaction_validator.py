import pytest
from app.schemas.transaction import TransactionParsedRow
from app.services.transaction_validator import validate_parsed_transactions
from app.core.exceptions import AppException

def test_validate_valid_rows_pass():
    rows = [
        TransactionParsedRow(
            transaction_date="2023-10-01",
            description="Test Vendor",
            amount="100.00",
            currency="USD",
            reference="REF123"
        )
    ]
    # Should not raise
    validate_parsed_transactions(rows)

def test_validate_empty_input_rejected():
    with pytest.raises(AppException) as excinfo:
        validate_parsed_transactions([])
    assert excinfo.value.status_code == 422
    assert "no data rows" in excinfo.value.detail

def test_validate_missing_required_columns_rejected():
    # Simulate a CSV row that had missing columns entirely (so they parsed as None)
    rows = [
        TransactionParsedRow(
            transaction_date=None,
            description=None,
            amount=None,
            currency=None,
            reference=None
        )
    ]
    with pytest.raises(AppException) as excinfo:
        validate_parsed_transactions(rows)
    assert excinfo.value.status_code == 422
    assert "transaction_date" in excinfo.value.detail
    assert "description" in excinfo.value.detail
    assert "amount" in excinfo.value.detail
    assert "currency" in excinfo.value.detail

def test_validate_missing_transaction_date():
    rows = [
        TransactionParsedRow(
            transaction_date=None,
            description="Test",
            amount="100.00",
            currency="USD"
        )
    ]
    with pytest.raises(AppException) as excinfo:
        validate_parsed_transactions(rows)
    assert "transaction_date" in excinfo.value.detail
    assert "description" not in excinfo.value.detail

def test_validate_missing_description():
    rows = [
        TransactionParsedRow(
            transaction_date="2023-10-01",
            description=None,
            amount="100.00",
            currency="USD"
        )
    ]
    with pytest.raises(AppException) as excinfo:
        validate_parsed_transactions(rows)
    assert "description" in excinfo.value.detail

def test_validate_missing_amount():
    rows = [
        TransactionParsedRow(
            transaction_date="2023-10-01",
            description="Test",
            amount=None,
            currency="USD"
        )
    ]
    with pytest.raises(AppException) as excinfo:
        validate_parsed_transactions(rows)
    assert "amount" in excinfo.value.detail

def test_validate_missing_currency():
    rows = [
        TransactionParsedRow(
            transaction_date="2023-10-01",
            description="Test",
            amount="100.00",
            currency=None
        )
    ]
    with pytest.raises(AppException) as excinfo:
        validate_parsed_transactions(rows)
    assert "currency" in excinfo.value.detail

def test_validate_blank_whitespace_values_rejected():
    rows = [
        TransactionParsedRow(
            transaction_date="   ",
            description="\t",
            amount="\n",
            currency=""
        )
    ]
    with pytest.raises(AppException) as excinfo:
        validate_parsed_transactions(rows)
    assert "transaction_date" in excinfo.value.detail
    assert "description" in excinfo.value.detail
    assert "amount" in excinfo.value.detail
    assert "currency" in excinfo.value.detail

def test_validate_optional_reference():
    rows = [
        TransactionParsedRow(
            transaction_date="2023-10-01",
            description="Test",
            amount="100.00",
            currency="USD",
            reference=None
        ),
        TransactionParsedRow(
            transaction_date="2023-10-02",
            description="Test2",
            amount="200.00",
            currency="USD",
            reference="  "
        )
    ]
    # Should not raise since reference is optional
    validate_parsed_transactions(rows)

def test_validate_multiple_rows_identifies_invalid_row():
    rows = [
        TransactionParsedRow(
            transaction_date="2023-10-01",
            description="Test1",
            amount="100.00",
            currency="USD"
        ),
        TransactionParsedRow(
            transaction_date="2023-10-02",
            description=None,  # Invalid
            amount="200.00",
            currency="USD"
        ),
        TransactionParsedRow(
            transaction_date="2023-10-03",
            description="Test3",
            amount=None,  # Invalid
            currency="USD"
        )
    ]
    with pytest.raises(AppException) as excinfo:
        validate_parsed_transactions(rows)
    
    assert "Validation failed for 2 row(s)" in excinfo.value.detail
    assert "Row 2: missing description" in excinfo.value.detail
    assert "Row 3: missing amount" in excinfo.value.detail
    assert "Row 1" not in excinfo.value.detail
