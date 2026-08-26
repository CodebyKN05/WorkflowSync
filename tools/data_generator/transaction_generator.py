import random
import datetime
from typing import List, Dict, Any

class TransactionRecord:
    def __init__(self, id: str, client_id: str, transaction_date: str, amount: float, description: str, reference: str, currency: str, source_file: str, created_at: str):
        self.id = id
        self.client_id = client_id
        self.transaction_date = transaction_date
        self.amount = amount
        self.description = description
        self.reference = reference
        self.currency = currency
        self.source_file = source_file
        self.created_at = created_at
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "transaction_date": self.transaction_date,
            "amount": self.amount,
            "description": self.description,
            "reference": self.reference,
            "currency": self.currency,
            "source_file": self.source_file,
            "created_at": self.created_at
        }

def generate_transactions(count: int, client_id: str, seed: int | None = None) -> List[TransactionRecord]:
    """
    Generates a list of fictional bank transaction records.
    The output is reproducible if a seed is provided.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    
    transactions = []
    
    base_descriptions = [
        "AWS PAYMENT", "OFFICE SUPPLIES", "CONSULTING FEE", 
        "LEGAL RETAINER", "MAINTENANCE SVC", "MARKETING EXP", 
        "SOFTWARE LICENSE", "UTILITY BILL", "LOGISTICS"
    ]
    
    for i in range(count):
        # Generate sensible fictional dates
        month = rng.randint(1, 11)
        day = rng.randint(1, 28)
        transaction_date_obj = datetime.date(2026, month, day)
        
        amount = round(rng.uniform(10.0, 10000.0), 2)
        
        # Add random suffix to make descriptions realistic and slightly varied
        description = f"{rng.choice(base_descriptions)} {rng.randint(100, 999)}"
        reference = f"REF-{rng.randint(100000, 999999)}"
        
        currency = rng.choice(["USD", "EUR", "GBP", "CAD", "AUD"])
        source_file = f"statement_{rng.choice(['jan', 'feb', 'mar', 'q1', 'q2'])}.csv"
        # created_at timestamp is deterministic
        created_at = f"{transaction_date_obj.isoformat()}T09:00:00Z"
        
        transactions.append(TransactionRecord(
            id=f"tx_{i+1}",
            client_id=client_id,
            transaction_date=transaction_date_obj.isoformat(),
            amount=amount,
            description=description,
            reference=reference,
            currency=currency,
            source_file=source_file,
            created_at=created_at
        ))
        
    return transactions
