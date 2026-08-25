import random
from typing import List, Dict, Any

class ClientRecord:
    def __init__(self, id: str, firm_id: str, name: str, industry: str, currency: str, created_at: str):
        self.id = id
        self.firm_id = firm_id
        self.name = name
        self.industry = industry
        self.currency = currency
        self.created_at = created_at
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "firm_id": self.firm_id,
            "name": self.name,
            "industry": self.industry,
            "currency": self.currency,
            "created_at": self.created_at
        }

def generate_clients(count: int, seed: int = None, firm_id: str = "firm_1") -> List[ClientRecord]:
    """
    Generates a list of fictional client records.
    The output is reproducible if a seed is provided.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    
    names = [
        "Acme Manufacturing", "Globex Consulting", "Stark Industries", 
        "Wayne Logistics", "Umbrella Retail", "Initech", 
        "Soylent Corp", "Massive Dynamic"
    ]
    industries = ["Manufacturing", "Consulting", "Technology", "Logistics", "Retail", "Software", "Food", "Research"]
    currencies = ["USD", "EUR", "GBP", "CAD", "AUD"]
    
    clients = []
    for i in range(count):
        base_name = names[i % len(names)]
        name_suffix = f" {i // len(names) + 1}" if i >= len(names) else ""
        
        clients.append(ClientRecord(
            id=f"client_{i+1}",
            firm_id=firm_id,
            name=f"{base_name}{name_suffix}",
            industry=rng.choice(industries),
            currency=rng.choice(currencies),
            created_at=f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T10:00:00Z"
        ))
    return clients
