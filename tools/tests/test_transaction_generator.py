import pytest
from tools.data_generator.transaction_generator import generate_transactions

def test_generate_transactions_count_and_client():
    txs = generate_transactions(count=5, client_id="client_99")
    
    assert len(txs) == 5
    assert txs[0].id == "tx_1"
    assert txs[-1].id == "tx_5"
    assert all(tx.client_id == "client_99" for tx in txs)

def test_generate_transactions_reproducibility():
    tx1 = generate_transactions(count=3, client_id="c1", seed=42)
    tx2 = generate_transactions(count=3, client_id="c1", seed=42)
    
    assert [t.to_dict() for t in tx1] == [t.to_dict() for t in tx2]

def test_generate_transactions_valid_data():
    txs = generate_transactions(count=10, client_id="c1", seed=1)
    
    for tx in txs:
        assert 10.0 <= tx.amount <= 10000.0
        assert len(tx.description) > 0
        assert tx.reference.startswith("REF-")
        assert len(tx.transaction_date) == 10  # Very basic ISO-8601 date length check
        assert tx.currency in ["USD", "EUR", "GBP", "CAD", "AUD"]
        assert tx.source_file.endswith(".csv")
        assert "T09:00:00Z" in tx.created_at
