import random
import datetime
from typing import List, Dict, Any
from tools.data_generator.vendor_generator import VendorRecord

class InvoiceRecord:
    def __init__(self, id: str, client_id: str, vendor: str, invoice_number: str, invoice_date: str, due_date: str, amount: float, currency: str, pdf_path: str, created_at: str):
        self.id = id
        self.client_id = client_id
        self.vendor = vendor
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        self.due_date = due_date
        self.amount = amount
        self.currency = currency
        self.pdf_path = pdf_path
        self.created_at = created_at
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "vendor": self.vendor,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "amount": self.amount,
            "currency": self.currency,
            "pdf_path": self.pdf_path,
            "created_at": self.created_at
        }

def generate_invoices(count: int, client_id: str, vendors: List[VendorRecord], seed: int | None = None) -> List[InvoiceRecord]:
    """
    Generates a list of fictional invoice records.
    The output is reproducible if a seed is provided.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    
    if not vendors:
        raise ValueError("At least one vendor must be provided.")
        
    invoices = []
    
    for i in range(count):
        # Pick a vendor from the supplied pool
        vendor = rng.choice(vendors)
        
        invoice_number = f"INV-{rng.randint(1000, 999999)}"
        amount = round(rng.uniform(50.0, 10000.0), 2)
        
        # Generate sensible fictional dates
        month = rng.randint(1, 11)
        day = rng.randint(1, 28)
        invoice_date_obj = datetime.date(2026, month, day)
        
        # Due dates are typically 15, 30, 45, or 60 days after invoice
        due_date_obj = invoice_date_obj + datetime.timedelta(days=rng.choice([15, 30, 45, 60]))
        
        invoice_date = invoice_date_obj.isoformat()
        due_date = due_date_obj.isoformat()
        
        # Deterministic placeholder path; no PDF is actually generated
        pdf_path = f"mock_storage/{client_id}/invoices/{invoice_number}.pdf"
        created_at = f"{invoice_date}T10:00:00Z"
        
        invoices.append(InvoiceRecord(
            id=f"inv_{i+1}",
            client_id=client_id,
            vendor=vendor.name,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            amount=amount,
            currency=rng.choice(["USD", "EUR", "GBP", "CAD", "AUD"]),
            pdf_path=pdf_path,
            created_at=created_at
        ))
        
    return invoices
