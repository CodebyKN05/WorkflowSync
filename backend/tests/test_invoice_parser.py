from datetime import date
from decimal import Decimal
from app.services.invoice_parser import parse_invoice_text

def test_parse_normal_invoice_all_fields():
    text = """
    Vendor: Acme Corp
    Invoice #12345
    Date: 2023-10-01
    Due Date: 2023-10-15
    Description          Amount
    Services             $1,000.00
    Total: $1,000.00
    """
    data = parse_invoice_text(text)
    assert data.vendor == "Acme Corp"
    assert data.invoice_number == "12345"
    assert data.invoice_date == date(2023, 10, 1)
    assert data.due_date == date(2023, 10, 15)
    assert data.total == Decimal('1000.00')
    assert data.currency == "USD"

def test_parse_invoice_number():
    assert parse_invoice_text("INV-999-ABC").invoice_number == "999-ABC"
    assert parse_invoice_text("Invoice No: 1234").invoice_number == "1234"
    assert parse_invoice_text("Invoice Number 555").invoice_number == "555"

def test_parse_vendor():
    assert parse_invoice_text("Vendor: Global Tech Inc\nInvoice 123").vendor == "Global Tech Inc"

def test_parse_invoice_date():
    assert parse_invoice_text("Invoice Date: 2024-01-31").invoice_date == date(2024, 1, 31)
    assert parse_invoice_text("Date: 12/31/2023").invoice_date == date(2023, 12, 31)

def test_parse_due_date():
    assert parse_invoice_text("Due Date: 2024-02-28").due_date == date(2024, 2, 28)
    assert parse_invoice_text("Due date: 01/15/2024").due_date == date(2024, 1, 15)

def test_parse_amount_and_currency():
    data = parse_invoice_text("Total: 5,432.10 EUR")
    assert data.total == Decimal('5432.10')
    assert data.currency == "EUR"

    data2 = parse_invoice_text("Amount Due: £ 999.99")
    assert data2.total == Decimal('999.99')
    assert data2.currency == "GBP"

def test_parse_missing_fields():
    text = "Just a random document with no invoice data."
    data = parse_invoice_text(text)
    assert data.vendor is None
    assert data.invoice_number is None
    assert data.invoice_date is None
    assert data.due_date is None
    assert data.total is None
    assert data.currency is None

def test_parse_malformed_text():
    # Should not crash on weird text
    text = "Total: $XYZ\nDate: 99-99-9999\nVendor: \nInvoice #"
    data = parse_invoice_text(text)
    # The parser handles these gracefully by catching exceptions or not matching
    assert data.total is None
    assert data.invoice_date is None
