from typing import List
from app.schemas.transaction import TransactionParsedRow
from app.core.exceptions import AppException
from fastapi import status

def validate_parsed_transactions(rows: List[TransactionParsedRow]) -> None:
    if not rows:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV contains no data rows."
        )

    errors = []
    
    for i, row in enumerate(rows):
        row_num = i + 1
        missing = []
        
        # Check required fields
        if not row.transaction_date or not row.transaction_date.strip():
            missing.append("transaction_date")
            
        if not row.description or not row.description.strip():
            missing.append("description")
            
        if not row.amount or not row.amount.strip():
            missing.append("amount")
            
        if not row.currency or not row.currency.strip():
            missing.append("currency")
            
        if missing:
            errors.append(f"Row {row_num}: missing {', '.join(missing)}")
            
    if errors:
        error_msg = f"Validation failed for {len(errors)} row(s). " + "; ".join(errors)
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg
        )
