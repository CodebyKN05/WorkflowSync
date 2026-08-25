from tools.data_generator.invoice_generator import generate_invoices
from tools.data_generator.vendor_generator import VendorRecord
import pytest

def test_generate_invoices_count_and_client():
    vendors = [VendorRecord("v1", "Test Vendor", "Software")]
    invoices = generate_invoices(count=5, client_id="client_42", vendors=vendors)
    
    assert len(invoices) == 5
    assert invoices[0].id == "inv_1"
    assert invoices[-1].id == "inv_5"
    assert all(inv.client_id == "client_42" for inv in invoices)

def test_generate_invoices_requires_vendors():
    with pytest.raises(ValueError, match="At least one vendor must be provided."):
        generate_invoices(count=5, client_id="client_1", vendors=[])

def test_generate_invoices_reproducibility():
    vendors = [
        VendorRecord("v1", "Test Vendor", "IT"), 
        VendorRecord("v2", "Another Vendor", "Legal")
    ]
    inv1 = generate_invoices(count=3, client_id="c1", vendors=vendors, seed=42)
    inv2 = generate_invoices(count=3, client_id="c1", vendors=vendors, seed=42)
    
    assert [i.to_dict() for i in inv1] == [i.to_dict() for i in inv2]

def test_generate_invoices_valid_data():
    vendors = [VendorRecord("v1", "Test Vendor", "IT")]
    invoices = generate_invoices(count=10, client_id="c1", vendors=vendors, seed=1)
    
    for inv in invoices:
        assert inv.vendor == "Test Vendor"
        assert 50.0 <= inv.amount <= 10000.0
        assert inv.currency in ["USD", "EUR", "GBP", "CAD", "AUD"]
        assert inv.invoice_number.startswith("INV-")
        assert inv.pdf_path.endswith(".pdf")
        assert "c1" in inv.pdf_path
        # Very basic check that due date comes after invoice date (lexicographically safe since ISO-8601)
        assert inv.due_date > inv.invoice_date
