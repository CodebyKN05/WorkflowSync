import random
import datetime
from typing import List, Dict, Any, Tuple, Optional
from tools.data_generator.invoice_generator import InvoiceRecord
from tools.data_generator.transaction_generator import TransactionRecord

class GroundTruthRecord:
    def __init__(self, invoice: Optional[str], expected_status: str, expected_transaction: Optional[str]):
        self.invoice = invoice
        self.expected_status = expected_status
        self.expected_transaction = expected_transaction
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice": self.invoice,
            "expected_status": self.expected_status,
            "expected_transaction": self.expected_transaction
        }

def choose_scenarios(count: int, percentages: Dict[str, float], seed: Optional[int] = None) -> List[str]:
    """
    Deterministically choose a list of scenarios based on the provided percentages.
    This guarantees exact proportions (rounded to nearest integer) rather than relying on probabilistic luck.
    """
    total_percentage = sum(percentages.values())
    if not (99.0 <= total_percentage <= 101.0):
        raise ValueError("Percentages must sum to exactly 100.")
        
    scenarios = []
    # Fill exactly according to weights
    for scenario, pct in percentages.items():
        qty = int(round(count * (pct / 100.0)))
        scenarios.extend([scenario] * qty)
        
    # Adjust for integer rounding errors to ensure exact total count
    if len(scenarios) < count:
        diff = count - len(scenarios)
        scenarios.extend(["MATCHED"] * diff)
    elif len(scenarios) > count:
        scenarios = scenarios[:count]
        
    rng = random.Random(seed) if seed is not None else random.Random()
    rng.shuffle(scenarios)
    return scenarios


def generate_scenario(
    scenario_type: str, 
    next_tx_id: int, 
    invoice: Optional[InvoiceRecord] = None, 
    client_id: Optional[str] = None,
    seed: Optional[int] = None
) -> Tuple[List[TransactionRecord], GroundTruthRecord]:
    """
    Generates synthetic bank transactions corresponding to a specific reconciliation scenario,
    and returns them alongside the required ground-truth record.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    transactions: List[TransactionRecord] = []
    
    # Determine the operating client_id
    effective_client_id = invoice.client_id if invoice else client_id
    if not effective_client_id:
        raise ValueError("Either an invoice or a client_id must be provided.")
        
    def create_base_tx(tx_id_str: str) -> TransactionRecord:
        if invoice is None:
            raise ValueError("Invoice must be provided for this scenario.")
            
        inv_date = datetime.date.fromisoformat(invoice.invoice_date)
        tx_date = inv_date + datetime.timedelta(days=rng.randint(1, 10))
        
        return TransactionRecord(
            id=tx_id_str,
            client_id=invoice.client_id,
            transaction_date=tx_date.isoformat(),
            amount=invoice.amount,
            description=f"{invoice.vendor.upper()} PAYMENT {rng.randint(100, 999)}",
            reference=f"REF-{rng.randint(100000, 999999)}",
            currency=invoice.currency,
            source_file="statement.csv",
            created_at=f"{tx_date.isoformat()}T10:00:00Z"
        )
    
    if scenario_type == "MATCHED":
        tx = create_base_tx(f"tx_{next_tx_id}")
        transactions.append(tx)
        gt = GroundTruthRecord(invoice.id if invoice else None, "MATCHED", tx.id)
        
    elif scenario_type == "AMOUNT_MISMATCH":
        tx = create_base_tx(f"tx_{next_tx_id}")
        # Skew the amount by 10%
        tx.amount = round(tx.amount * rng.choice([0.90, 1.10]), 2)
        transactions.append(tx)
        gt = GroundTruthRecord(invoice.id if invoice else None, "AMOUNT_MISMATCH", tx.id)
        
    elif scenario_type == "VENDOR_MISMATCH":
        tx = create_base_tx(f"tx_{next_tx_id}")
        # Generate a completely unrelated description
        tx.description = rng.choice(["OFFICE SUPPLIES", "MAINTENANCE SVC", "CONSULTING FEE"])
        transactions.append(tx)
        gt = GroundTruthRecord(invoice.id if invoice else None, "VENDOR_MISMATCH", tx.id)
        
    elif scenario_type == "DATE_MISMATCH":
        tx = create_base_tx(f"tx_{next_tx_id}")
        # Skew date by 2-6 months
        inv_date = datetime.date.fromisoformat(invoice.invoice_date if invoice else "2026-01-01")
        tx_date = inv_date + datetime.timedelta(days=rng.randint(60, 180))
        tx.transaction_date = tx_date.isoformat()
        transactions.append(tx)
        gt = GroundTruthRecord(invoice.id if invoice else None, "DATE_MISMATCH", tx.id)
        
    elif scenario_type == "MISSING_PAYMENT":
        # No transactions are generated
        gt = GroundTruthRecord(invoice.id if invoice else None, "MISSING_PAYMENT", None)
        
    elif scenario_type == "DUPLICATE_PAYMENT":
        tx1 = create_base_tx(f"tx_{next_tx_id}")
        tx2 = create_base_tx(f"tx_{next_tx_id + 1}")
        
        # Make the second transaction identical except for its ID
        tx2.transaction_date = tx1.transaction_date
        tx2.amount = tx1.amount
        tx2.description = tx1.description
        
        transactions.extend([tx1, tx2])
        # Ambiguity Resolution: Schema requires a single string. We pick the first transaction.
        gt = GroundTruthRecord(invoice.id if invoice else None, "DUPLICATE_PAYMENT", tx1.id)
        
    elif scenario_type == "UNRELATED_TRANSACTION":
        # Generates a transaction entirely unrelated to any invoice
        month = rng.randint(1, 11)
        day = rng.randint(1, 28)
        tx_date_obj = datetime.date(2026, month, day)
        
        tx = TransactionRecord(
            id=f"tx_{next_tx_id}",
            client_id=effective_client_id,
            transaction_date=tx_date_obj.isoformat(),
            amount=round(rng.uniform(10.0, 5000.0), 2),
            description=f"MISC BANK FEE {rng.randint(100, 999)}",
            reference=f"REF-{rng.randint(100000, 999999)}",
            currency="USD",
            source_file="statement.csv",
            created_at=f"{tx_date_obj.isoformat()}T09:00:00Z"
        )
        transactions.append(tx)
        # Ambiguity Resolution: Schema requires an invoice ID. None exists.
        gt = GroundTruthRecord(None, "UNRELATED_TRANSACTION", tx.id)
        
    else:
        raise ValueError(f"Unknown scenario type: {scenario_type}")
        
    return transactions, gt
