from dataclasses import dataclass
from datetime import date

@dataclass
class DateComparisonResult:
    """
    Represents the result of a date comparison between an invoice date
    and a transaction date.
    """
    is_exact_match: bool
    days_difference: int

def compare_dates(invoice_date: date, transaction_date: date) -> DateComparisonResult:
    """
    Evaluates the temporal relationship between an invoice date and a transaction date.
    
    The project Source of Truth does not currently define a date tolerance. 
    Therefore, this service calculates the raw difference in days and evaluates 
    an exact match strictness.
    """
    # Calculate difference in days (absolute magnitude of distance)
    days_difference = abs((transaction_date - invoice_date).days)
    
    return DateComparisonResult(
        is_exact_match=(days_difference == 0),
        days_difference=days_difference
    )
