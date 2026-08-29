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
