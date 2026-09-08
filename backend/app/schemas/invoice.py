import uuid
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

class InvoiceUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    message: str
    extracted_text: str
    extracted_data: InvoiceExtractedData
    status: str

from datetime import datetime

class InvoiceListResponse(BaseModel):
    id: uuid.UUID
    vendor: str
    amount: Decimal
    currency: str
    invoice_date: date
    status: str
    created_at: datetime
