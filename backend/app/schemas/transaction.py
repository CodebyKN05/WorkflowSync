from typing import Optional
from pydantic import BaseModel

class TransactionParsedRow(BaseModel):
    transaction_date: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[str] = None
    currency: Optional[str] = None
    reference: Optional[str] = None
