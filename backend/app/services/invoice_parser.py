import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from app.schemas.invoice import InvoiceExtractedData

def parse_invoice_text(text: str) -> InvoiceExtractedData:
    """
    Deterministic parser for extracted invoice text.
    Extracts invoice_number, vendor, invoice_date, due_date, total, currency.
    """
    data = InvoiceExtractedData()

    # 1. Invoice Number
    inv_num_match = re.search(r'(?i)(?:invoice\s*(?:#|no[.:]?|number:?)\s*|inv-)([a-z0-9\-]+)', text)
    if inv_num_match:
        data.invoice_number = inv_num_match.group(1).strip()

    # 2. Vendor
    vendor_match = re.search(r'(?i)vendor:\s*(.+?)(?=\n|$)', text)
    if vendor_match:
        data.vendor = vendor_match.group(1).strip()

    # 3. Dates (Invoice Date, Due Date)
    date_match = re.search(r'(?i)(?:invoice\s*)?date:\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', text)
    if date_match:
        data.invoice_date = _parse_date(date_match.group(1))

    due_date_match = re.search(r'(?i)due\s*date:\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', text)
    if due_date_match:
        data.due_date = _parse_date(due_date_match.group(1))

    # 4. Total and Currency
    total_match = re.search(r'(?i)(?:total|amount(?:\s*due)?):\s*([a-z$€£]*)\s*([\d,]+\.\d{2})\s*([a-z]*)', text)
    if total_match:
        prefix_curr = total_match.group(1).strip()
        amount_str = total_match.group(2).replace(',', '')
        suffix_curr = total_match.group(3).strip()

        try:
            data.total = Decimal(amount_str)
        except Exception:
            pass

        currency = prefix_curr or suffix_curr
        if currency:
            currency = currency.upper()
            if currency == '$':
                data.currency = 'USD'
            elif currency == '€':
                data.currency = 'EUR'
            elif currency == '£':
                data.currency = 'GBP'
            else:
                data.currency = currency

    return data

def _parse_date(date_str: str) -> Optional[date]:
    date_str = date_str.strip()
    try:
        if '-' in date_str:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        elif '/' in date_str:
            return datetime.strptime(date_str, '%m/%d/%Y').date()
    except ValueError:
        pass
    return None
