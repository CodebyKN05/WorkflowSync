import re
from typing import List
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from app.schemas.transaction import TransactionParsedRow, TransactionNormalizedRow
from app.core.exceptions import AppException
from fastapi import status

DATE_FORMATS = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']

def normalize_transactions(rows: List[TransactionParsedRow]) -> List[TransactionNormalizedRow]:
    normalized_rows = []
    errors = []

    for i, row in enumerate(rows):
        row_num = i + 1
        
        # We assume validation has already verified that required fields are present.
        # This allows us to safely cast/strip.
        try:
            from typing import cast
            norm_date = _normalize_date(cast(str, row.transaction_date))
            norm_amount = _normalize_amount(cast(str, row.amount))
            norm_currency = _normalize_currency(cast(str, row.currency))
            norm_desc = row.description.strip() if row.description else ""
            
            norm_ref = None
            if row.reference and row.reference.strip():
                norm_ref = row.reference.strip()

            normalized_rows.append(TransactionNormalizedRow(
                transaction_date=norm_date,
                description=norm_desc,
                amount=norm_amount,
                currency=norm_currency,
                reference=norm_ref
            ))
        except ValueError as e:
            errors.append(f"Row {row_num}: {str(e)}")
            
    if errors:
        error_msg = f"Normalization failed for {len(errors)} row(s). " + "; ".join(errors)
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg
        )
        
    return normalized_rows

def _normalize_date(date_str: str) -> date:
    date_str = date_str.strip()
    parsed_dates = set()
    
    for fmt in DATE_FORMATS:
        try:
            parsed_dates.add(datetime.strptime(date_str, fmt).date())
        except ValueError:
            pass
            
    if len(parsed_dates) == 1:
        return parsed_dates.pop()
    elif len(parsed_dates) > 1:
        raise ValueError(f"Ambiguous date format: {date_str}")
    else:
        raise ValueError(f"Invalid date format: {date_str}")

def _normalize_amount(amount_str: str) -> Decimal:
    amount_str = amount_str.strip()
    # Remove currency symbols and commas
    clean_str = re.sub(r'[$,£€]', '', amount_str)
    clean_str = clean_str.replace(',', '')
    
    try:
        return Decimal(clean_str)
    except InvalidOperation:
        raise ValueError(f"Invalid amount format: {amount_str}")

def _normalize_currency(currency_str: str) -> str:
    currency_str = currency_str.strip().upper()
    # Basic check for 3 character code, we don't validate against a full enum here
    if len(currency_str) != 3 or not currency_str.isalpha():
        raise ValueError(f"Invalid currency format: {currency_str}")
    return currency_str
