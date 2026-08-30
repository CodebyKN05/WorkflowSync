from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal
import uuid

class ResolveRequest(BaseModel):
    transaction_id: uuid.UUID

class InvoiceReviewResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    vendor: str
    invoice_date: date
    amount: Decimal
    currency: str

    class Config:
        from_attributes = True

class TransactionReviewResponse(BaseModel):
    id: uuid.UUID
    description: str
    transaction_date: date
    amount: Decimal
    currency: str
    reference: Optional[str] = None

    class Config:
        from_attributes = True

class ReviewCandidateResponse(BaseModel):
    id: uuid.UUID
    score: Decimal
    status: str
    reason: str
    invoice: InvoiceReviewResponse
    transaction: TransactionReviewResponse

    class Config:
        from_attributes = True
