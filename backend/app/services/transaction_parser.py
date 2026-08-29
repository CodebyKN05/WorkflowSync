import csv
import io
from typing import List
from app.schemas.transaction import TransactionParsedRow

# Mapping of normalized (lowercase, stripped) CSV header names to internal field names
HEADER_ALIASES = {
    "date": "transaction_date",
    "transaction date": "transaction_date",
    "description": "description",
    "details": "description",
    "amount": "amount",
    "transaction amount": "amount",
    "value": "amount",
    "currency": "currency",
    "reference": "reference",
    "reference number": "reference",
    "ref": "reference"
}

def parse_transaction_csv(csv_text: str) -> List[TransactionParsedRow]:
    """
    Parses a raw CSV string and maps known columns to TransactionParsedRow.
    Additional or unmapped columns are ignored.
    """
    if not csv_text.strip():
        return []

    # Use io.StringIO to treat the string as a file object for the csv module
    f = io.StringIO(csv_text.strip())
    
    # Peek at the dialect/headers using standard reader to handle missing headers gracefully
    reader = csv.reader(f)
    try:
        raw_headers = next(reader)
    except StopIteration:
        return []

    # Normalize headers for alias matching
    mapped_fieldnames = []
    for header in raw_headers:
        if header is None:
            mapped_fieldnames.append(None)
            continue
        
        normalized = header.strip().lower()
        if normalized in HEADER_ALIASES:
            mapped_fieldnames.append(HEADER_ALIASES[normalized])
        else:
            # Keep original or ignore - for DictReader we just need unique keys, 
            # but we only care about mapping to our schema.
            mapped_fieldnames.append(normalized)

    # Re-seek and use DictReader with our mapped fieldnames
    f.seek(0)
    # Skip the header row since we already mapped fieldnames manually
    next(f)
    
    dict_reader = csv.DictReader(f, fieldnames=mapped_fieldnames)
    
    parsed_rows = []
    for row in dict_reader:
        # Extract only the mapped fields, leaving others behind
        parsed_row = TransactionParsedRow(
            transaction_date=row.get("transaction_date") and row["transaction_date"].strip(),
            description=row.get("description") and row["description"].strip(),
            amount=row.get("amount") and row["amount"].strip(),
            currency=row.get("currency") and row["currency"].strip(),
            reference=row.get("reference") and row["reference"].strip()
        )
        parsed_rows.append(parsed_row)
        
    return parsed_rows
