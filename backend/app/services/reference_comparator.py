from dataclasses import dataclass
from typing import Optional

@dataclass
class ReferenceComparisonResult:
    """
    Represents the result of a reference comparison between an invoice
    and a transaction.
    """
    is_exact_match: bool

def compare_references(invoice_reference: Optional[str], transaction_reference: Optional[str]) -> ReferenceComparisonResult:
    """
    Evaluates the deterministic relationship between an invoice reference and a transaction reference.
    
    The comparison uses NORMALIZED EXACT MATCHING:
    - Trims surrounding whitespace.
    - Performs case-insensitive equality check.
    - Missing or completely blank references never match.
    - Substring or fuzzy matching is strictly avoided.
    """
    if not invoice_reference or not transaction_reference:
        return ReferenceComparisonResult(is_exact_match=False)
        
    inv_norm = invoice_reference.strip().lower()
    txn_norm = transaction_reference.strip().lower()
    
    if not inv_norm or not txn_norm:
        return ReferenceComparisonResult(is_exact_match=False)
        
    return ReferenceComparisonResult(is_exact_match=(inv_norm == txn_norm))
