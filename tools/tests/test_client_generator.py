from tools.data_generator.client_generator import generate_clients

def test_generate_clients_count():
    clients = generate_clients(count=5)
    assert len(clients) == 5
    assert clients[0].id == "client_1"
    assert clients[-1].id == "client_5"

def test_generate_clients_reproducibility():
    clients1 = generate_clients(count=3, seed=42)
    clients2 = generate_clients(count=3, seed=42)
    
    assert [c.to_dict() for c in clients1] == [c.to_dict() for c in clients2]

def test_generate_clients_fictional_data():
    clients = generate_clients(count=10, seed=1)
    
    for c in clients:
        assert c.firm_id == "firm_1"
        assert c.currency in ["USD", "EUR", "GBP", "CAD", "AUD"]
        assert c.industry in ["Manufacturing", "Consulting", "Technology", "Logistics", "Retail", "Software", "Food", "Research"]
        assert "T10:00:00Z" in c.created_at
