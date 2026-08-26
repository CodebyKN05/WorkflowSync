import pytest
from tools.data_generator.invoice_generator import InvoiceRecord
from tools.data_generator.scenario_generator import generate_scenario, choose_scenarios

@pytest.fixture
def sample_invoice():
    return InvoiceRecord(
        id="inv_1",
        client_id="client_42",
        invoice_number="INV-100",
        vendor="Acme Corp",
        invoice_date="2026-08-01",
        due_date="2026-08-31",
        amount=500.00,
        currency="USD",
        pdf_path="mock/path.pdf",
        created_at="2026-08-01T00:00:00Z"
    )

def test_choose_scenarios_exact_proportions():
    percentages = {
        "MATCHED": 50.0,
        "AMOUNT_MISMATCH": 20.0,
        "MISSING_PAYMENT": 30.0
    }
    
    # Generate exactly 10 scenarios
    scenarios = choose_scenarios(count=10, percentages=percentages, seed=42)
    
    assert len(scenarios) == 10
    assert scenarios.count("MATCHED") == 5
    assert scenarios.count("AMOUNT_MISMATCH") == 2
    assert scenarios.count("MISSING_PAYMENT") == 3

def test_choose_scenarios_invalid_percentages():
    percentages = {"MATCHED": 50.0}
    with pytest.raises(ValueError, match="Percentages must sum to exactly 100."):
        choose_scenarios(10, percentages)

def test_generate_matched_scenario(sample_invoice):
    txs, gt = generate_scenario("MATCHED", 1, invoice=sample_invoice)
    assert len(txs) == 1
    assert txs[0].amount == 500.00
    assert "ACME" in txs[0].description.upper()
    assert gt.expected_status == "MATCHED"
    assert gt.expected_transaction == txs[0].id
    assert gt.invoice == sample_invoice.id

def test_generate_missing_payment_scenario(sample_invoice):
    txs, gt = generate_scenario("MISSING_PAYMENT", 1, invoice=sample_invoice)
    assert len(txs) == 0
    assert gt.expected_status == "MISSING_PAYMENT"
    assert gt.expected_transaction is None
    assert gt.invoice == sample_invoice.id

def test_generate_duplicate_payment_scenario(sample_invoice):
    txs, gt = generate_scenario("DUPLICATE_PAYMENT", 1, invoice=sample_invoice)
    assert len(txs) == 2
    assert txs[0].amount == txs[1].amount == 500.00
    assert txs[0].transaction_date == txs[1].transaction_date
    assert gt.expected_status == "DUPLICATE_PAYMENT"
    assert gt.expected_transaction == txs[0].id

def test_generate_amount_mismatch_scenario(sample_invoice):
    txs, gt = generate_scenario("AMOUNT_MISMATCH", 1, invoice=sample_invoice, seed=42)
    assert len(txs) == 1
    assert txs[0].amount != 500.00
    assert gt.expected_status == "AMOUNT_MISMATCH"
    assert gt.expected_transaction == txs[0].id

def test_generate_vendor_mismatch_scenario(sample_invoice):
    txs, gt = generate_scenario("VENDOR_MISMATCH", 1, invoice=sample_invoice, seed=42)
    assert len(txs) == 1
    assert txs[0].amount == 500.00
    assert "ACME" not in txs[0].description.upper()
    assert gt.expected_status == "VENDOR_MISMATCH"

def test_generate_date_mismatch_scenario(sample_invoice):
    txs, gt = generate_scenario("DATE_MISMATCH", 1, invoice=sample_invoice, seed=42)
    assert len(txs) == 1
    assert txs[0].amount == 500.00
    assert gt.expected_status == "DATE_MISMATCH"

def test_generate_unrelated_transaction_scenario():
    txs, gt = generate_scenario("UNRELATED_TRANSACTION", 1, client_id="client_99")
    assert len(txs) == 1
    assert txs[0].client_id == "client_99"
    assert gt.expected_status == "UNRELATED_TRANSACTION"
    assert gt.invoice is None
    assert gt.expected_transaction == txs[0].id

def test_generate_scenario_reproducibility(sample_invoice):
    txs1, gt1 = generate_scenario("MATCHED", 1, invoice=sample_invoice, seed=123)
    txs2, gt2 = generate_scenario("MATCHED", 1, invoice=sample_invoice, seed=123)
    
    assert [t.to_dict() for t in txs1] == [t.to_dict() for t in txs2]
    assert gt1.to_dict() == gt2.to_dict()
