from tools.data_generator.vendor_generator import generate_vendors

def test_generate_vendors_count():
    vendors = generate_vendors(count=5)
    assert len(vendors) == 5
    assert vendors[0].id == "vendor_1"
    assert vendors[-1].id == "vendor_5"

def test_generate_vendors_reproducibility():
    vendors1 = generate_vendors(count=4, seed=123)
    vendors2 = generate_vendors(count=4, seed=123)
    
    assert [v.to_dict() for v in vendors1] == [v.to_dict() for v in vendors2]

def test_generate_vendors_fictional_data():
    vendors = generate_vendors(count=10, seed=42)
    
    for v in vendors:
        assert v.category in ["Software", "Office Supplies", "Marketing", "Legal", "Consulting", "Maintenance", "Logistics", "Utilities", "Hardware"]
        assert len(v.name) > 0
