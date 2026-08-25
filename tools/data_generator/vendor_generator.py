import random
from typing import List, Dict, Any

class VendorRecord:
    def __init__(self, id: str, name: str, category: str):
        self.id = id
        self.name = name
        self.category = category
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category
        }

def generate_vendors(count: int, seed: int | None = None) -> List[VendorRecord]:
    """
    Generates a list of fictional vendor records.
    The output is reproducible if a seed is provided.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    
    prefixes = ["Alpha", "Beta", "Gamma", "Omega", "Apex", "Prime", "Summit", "Nexus", "Global", "United", "Acme", "Zenith"]
    suffixes = ["Solutions", "Services", "Technologies", "Logistics", "Supplies", "Consulting", "Group", "Partners", "Corp", "Inc"]
    categories = ["Software", "Office Supplies", "Marketing", "Legal", "Consulting", "Maintenance", "Logistics", "Utilities", "Hardware"]
    
    vendors = []
    for i in range(count):
        # Generate a fictional name combining prefixes and suffixes
        prefix = rng.choice(prefixes)
        suffix = rng.choice(suffixes)
        base_name = f"{prefix} {suffix}"
        
        # Ensure we don't just generate the exact same string endlessly if count is huge
        name_suffix = f" {i + 1}" if i >= (len(prefixes) * len(suffixes)) else ""
        
        vendors.append(VendorRecord(
            id=f"vendor_{i+1}",
            name=f"{base_name}{name_suffix}",
            category=rng.choice(categories)
        ))
        
    return vendors
