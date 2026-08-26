import csv
from typing import List
from tools.data_generator.transaction_generator import TransactionRecord

def generate_bank_csv(transactions: List[TransactionRecord], output_path: str) -> None:
    """
    Generates a client-specific bank CSV file from a list of TransactionRecords.
    """
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "date", "description", "amount", "currency"])
        
        for tx in transactions:
            # Note: amount is preserved exactly as represented in TransactionRecord.
            writer.writerow([
                tx.id,
                tx.transaction_date,
                tx.description,
                f"{tx.amount:.2f}",
                tx.currency
            ])
