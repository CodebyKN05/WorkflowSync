from app.services.transaction_parser import parse_transaction_csv

def test_parse_valid_csv_all_fields():
    csv_text = """transaction_date,description,amount,currency,reference
2023-10-01,Office Supplies,-50.00,USD,REF123
"""
    rows = parse_transaction_csv(csv_text)
    assert len(rows) == 1
    assert rows[0].transaction_date == "2023-10-01"
    assert rows[0].description == "Office Supplies"
    assert rows[0].amount == "-50.00"
    assert rows[0].currency == "USD"
    assert rows[0].reference == "REF123"

def test_parse_multiple_rows():
    csv_text = """Date,Description,Amount,Currency
2023-10-01,Vendor A,-10.00,USD
2023-10-02,Vendor B,-20.00,USD
"""
    rows = parse_transaction_csv(csv_text)
    assert len(rows) == 2
    assert rows[0].amount == "-10.00"
    assert rows[1].amount == "-20.00"

def test_parse_supported_header_aliases():
    csv_text = """Transaction Date,Details,Transaction Amount,Currency,Reference Number
2023-10-01,Vendor A,-100.00,EUR,999
"""
    rows = parse_transaction_csv(csv_text)
    assert len(rows) == 1
    assert rows[0].transaction_date == "2023-10-01"
    assert rows[0].description == "Vendor A"
    assert rows[0].amount == "-100.00"
    assert rows[0].currency == "EUR"
    assert rows[0].reference == "999"

def test_parse_optional_reference_field():
    csv_text = """Date,Description,Amount,Currency
2023-10-01,Vendor A,-10.00,USD
"""
    rows = parse_transaction_csv(csv_text)
    assert len(rows) == 1
    assert rows[0].reference is None

def test_parse_empty_csv_input():
    assert len(parse_transaction_csv("")) == 0
    assert len(parse_transaction_csv("   \n  ")) == 0
    assert len(parse_transaction_csv("Date,Description\n")) == 0 # Only headers, no data rows

def test_parse_csv_with_unmapped_columns():
    csv_text = """Date,Description,ExtraCol,Amount,AnotherExtra
2023-10-01,Vendor A,Ignore me,-10.00,Ignore too
"""
    rows = parse_transaction_csv(csv_text)
    assert len(rows) == 1
    assert rows[0].transaction_date == "2023-10-01"
    assert rows[0].description == "Vendor A"
    assert rows[0].amount == "-10.00"
    # Ensure ExtraCol and AnotherExtra don't cause issues and are ignored
    assert not hasattr(rows[0], "extracol")
