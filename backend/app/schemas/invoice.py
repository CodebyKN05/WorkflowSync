from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal

class InvoiceExtractedData(BaseModel):
    invoice_number: Optional[str] = None
    vendor: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    total: Optional[Decimal] = None
    currency: Optional[str] = None
