from typing import Optional
from pydantic import BaseModel
from datetime import date
from decimal import Decimal

class TransactionParsedRow(BaseModel):
    transaction_date: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    currency: Optional[str] = None
    reference: Optional[str] = None

class TransactionNormalizedRow(BaseModel):
    transaction_date: date
    description: str
    amount: Decimal
    currency: str
    reference: Optional[str] = None

from datetime import datetime
import uuid

class TransactionListResponse(BaseModel):
    id: uuid.UUID
    transaction_date: date
    description: str
    amount: Decimal
    currency: str
    reference: Optional[str] = None
    source_file: Optional[str] = None
    created_at: datetime
