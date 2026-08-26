import os
import csv
import tempfile
import pytest
from tools.data_generator.transaction_generator import TransactionRecord
from tools.data_generator.csv_generator import generate_bank_csv

@pytest.fixture
def sample_transactions():
    return [
        TransactionRecord(
            id="TX-001",
            client_id="client_1",
            transaction_date="2026-08-04",
            amount=-1500.00,
            description="AWS PAYMENT",
            reference="REF-1",
            currency="USD",
            source_file="stmt1.csv",
            created_at="2026-08-04T00:00:00Z"
        ),
        TransactionRecord(
            id="TX-002",
            client_id="client_1",
            transaction_date="2026-08-06",
            amount=1240.00,
            description="MICROSOFT, INC.",
            reference="REF-2",
            currency="USD",
            source_file="stmt1.csv",
            created_at="2026-08-06T00:00:00Z"
        )
    ]

def test_csv_creation_and_headers(sample_transactions):
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "bank.csv")
        generate_bank_csv(sample_transactions, csv_path)
        
        assert os.path.exists(csv_path)
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == ["transaction_id", "date", "description", "amount", "currency"]

def test_csv_data_preservation(sample_transactions):
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "bank.csv")
        generate_bank_csv(sample_transactions, csv_path)
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader) # skip headers
            rows = list(reader)
            
            assert len(rows) == 2
            
            # Row 1
            assert rows[0][0] == "TX-001"
            assert rows[0][1] == "2026-08-04"
            assert rows[0][2] == "AWS PAYMENT"
            assert rows[0][3] == "-1500.00"
            assert rows[0][4] == "USD"
            
            # Row 2 (checking comma in description)
            assert rows[1][2] == "MICROSOFT, INC."
            assert rows[1][3] == "1240.00"

def test_csv_empty_transactions():
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "empty.csv")
        generate_bank_csv([], csv_path)
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0] == ["transaction_id", "date", "description", "amount", "currency"]

def test_deterministic_output(sample_transactions):
    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path1 = os.path.join(temp_dir, "bank1.csv")
        csv_path2 = os.path.join(temp_dir, "bank2.csv")
        
        generate_bank_csv(sample_transactions, csv_path1)
        generate_bank_csv(sample_transactions, csv_path2)
        
        with open(csv_path1, "r", encoding="utf-8") as f1, open(csv_path2, "r", encoding="utf-8") as f2:
            assert f1.read() == f2.read()
