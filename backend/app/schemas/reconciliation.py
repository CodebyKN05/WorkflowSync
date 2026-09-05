from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
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

class ReconciliationRunResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    matched_count: int
    review_count: int
    unmatched_count: int
    duplicate_count: int

    class Config:
        from_attributes = True
