import os
import tempfile
import fitz
import csv
import pytest

from tools.data_generator.orchestrator import generate_dataset, SyntheticDataset

@pytest.fixture
def default_config():
    return {
        "client_count": 2,
        "vendor_count": 3,
        "invoices_per_client": 5,
        "scenario_percentages": {
            "MATCHED": 50,
            "AMOUNT_MISMATCH": 10,
            "VENDOR_MISMATCH": 10,
            "MISSING_PAYMENT": 10,
            "DUPLICATE_PAYMENT": 10,
            "UNRELATED_TRANSACTION": 10,
            "DATE_MISMATCH": 0
        }
    }

def test_deterministic_logical_dataset(default_config):
    with tempfile.TemporaryDirectory() as temp_dir:
        dir1 = os.path.join(temp_dir, "run1")
        dir2 = os.path.join(temp_dir, "run2")
        
        ds1 = generate_dataset(master_seed=42, output_dir=dir1, **default_config)
        ds2 = generate_dataset(master_seed=42, output_dir=dir2, **default_config)
        
        # Test logical equality (excluding filesystem paths)
        assert [c.to_dict() for c in ds1.clients] == [c.to_dict() for c in ds2.clients]
        assert [v.to_dict() for v in ds1.vendors] == [v.to_dict() for v in ds2.vendors]
        
        # We must exclude pdf_path from invoice comparison because it's modified by the orchestrator and depends on output_dir
        inv1_dicts = [i.to_dict() for i in ds1.invoices]
        inv2_dicts = [i.to_dict() for i in ds2.invoices]
        for idx in range(len(inv1_dicts)):
            inv1_dicts[idx]["pdf_path"] = ""
            inv2_dicts[idx]["pdf_path"] = ""
        assert inv1_dicts == inv2_dicts
        
        assert [t.to_dict() for t in ds1.transactions] == [t.to_dict() for t in ds2.transactions]
        assert [g.__dict__ for g in ds1.ground_truth] == [g.__dict__ for g in ds2.ground_truth]
        
        # Test exact scenario proportion
        # 10 invoices total.
        matched_count = sum(1 for g in ds1.ground_truth if g.expected_status == "MATCHED")
        assert matched_count == 5

def test_different_seeds_produce_different_data(default_config):
    with tempfile.TemporaryDirectory() as temp_dir:
        ds1 = generate_dataset(master_seed=42, output_dir=temp_dir, **default_config)
        ds2 = generate_dataset(master_seed=99, output_dir=temp_dir, **default_config)
        
        # Different seeds should produce different generated amounts
        assert ds1.invoices[0].amount != ds2.invoices[0].amount

def test_deterministic_artifacts(default_config):
    with tempfile.TemporaryDirectory() as temp_dir:
        dir1 = os.path.join(temp_dir, "run1")
        dir2 = os.path.join(temp_dir, "run2")
        
        ds1 = generate_dataset(master_seed=123, output_dir=dir1, **default_config)
        ds2 = generate_dataset(master_seed=123, output_dir=dir2, **default_config)
        
        # Test CSV equality
        for csv1, csv2 in zip(ds1.csv_paths, ds2.csv_paths):
            with open(csv1, "r", encoding="utf-8") as f1, open(csv2, "r", encoding="utf-8") as f2:
                content1 = f1.read()
                content2 = f2.read()
                assert content1 == content2
                # Verify no invoice IDs in CSV
                assert "INV-" not in content1
                
        # Test PDF visual determinism (extracted text)
        for pdf1, pdf2 in zip(ds1.pdf_paths, ds2.pdf_paths):
            doc1 = fitz.open(pdf1)
            text1 = doc1[0].get_text()
            doc1.close()
            
            doc2 = fitz.open(pdf2)
            text2 = doc2[0].get_text()
            doc2.close()
            
            assert text1 == text2

def test_unrelated_transaction_semantics(default_config):
    # Force 100% unrelated transaction to test semantics
    config = default_config.copy()
    config["scenario_percentages"] = {"UNRELATED_TRANSACTION": 100}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        ds = generate_dataset(master_seed=777, output_dir=temp_dir, **config)
        
        for gt in ds.ground_truth:
            # Unrelated means the invoice has NO expected matching transaction.
            assert gt.expected_status == "UNRELATED_TRANSACTION"
            assert gt.expected_transaction is not None
            assert gt.invoice is None
