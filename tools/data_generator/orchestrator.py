import hashlib
import os
from typing import List, Dict
from collections import defaultdict
from dataclasses import dataclass

from tools.data_generator.client_generator import ClientRecord, generate_clients
from tools.data_generator.vendor_generator import VendorRecord, generate_vendors
from tools.data_generator.invoice_generator import InvoiceRecord, generate_invoices
from tools.data_generator.transaction_generator import TransactionRecord
from tools.data_generator.scenario_generator import GroundTruthRecord, choose_scenarios, generate_scenario
from tools.data_generator.pdf_generator import generate_pdf_for_invoice
from tools.data_generator.csv_generator import generate_bank_csv

@dataclass
class SyntheticDataset:
    clients: List[ClientRecord]
    vendors: List[VendorRecord]
    invoices: List[InvoiceRecord]
    transactions: List[TransactionRecord]
    ground_truth: List[GroundTruthRecord]
    pdf_paths: List[str]
    csv_paths: List[str]

def _derive_seed(master_seed: int, context: str) -> int:
    """Derives a deterministic sub-seed based on the master seed and context string."""
    hash_input = f"{master_seed}:{context}".encode('utf-8')
    return int(hashlib.sha256(hash_input).hexdigest()[:8], 16)

def generate_dataset(
    master_seed: int,
    client_count: int,
    vendor_count: int,
    invoices_per_client: int,
    scenario_percentages: Dict[str, float],
    output_dir: str
) -> SyntheticDataset:
    
    # 1. Generate Clients
    client_seed = _derive_seed(master_seed, "clients")
    clients = generate_clients(count=client_count, seed=client_seed)
    
    # 2. Generate Vendors
    vendor_seed = _derive_seed(master_seed, "vendors")
    vendors = generate_vendors(count=vendor_count, seed=vendor_seed)
    
    # 3. Generate Invoices
    invoices = []
    for i, client in enumerate(clients):
        inv_seed = _derive_seed(master_seed, f"invoices_client_{i}")
        client_invoices = generate_invoices(
            count=invoices_per_client,
            client_id=client.id,
            vendors=vendors,
            seed=inv_seed
        )
        invoices.extend(client_invoices)
        
    # 4. Choose Scenarios
    scenario_seed = _derive_seed(master_seed, "scenarios")
    total_invoices = len(invoices)
    scenarios = choose_scenarios(count=total_invoices, percentages=scenario_percentages, seed=scenario_seed)
    
    # 5. Generate Scenario Transactions & Ground Truth
    transactions = []
    ground_truth = []
    next_tx_id = 1
    
    for i, (invoice, scenario_type) in enumerate(zip(invoices, scenarios)):
        tx_seed = _derive_seed(master_seed, f"tx_invoice_{i}")
        
        scenario_txs, gt_record = generate_scenario(
            scenario_type=scenario_type,
            next_tx_id=next_tx_id,
            invoice=invoice,
            client_id=invoice.client_id,
            seed=tx_seed
        )
        
        transactions.extend(scenario_txs)
        ground_truth.append(gt_record)
        next_tx_id += len(scenario_txs)
        
    # 6. Generate PDFs
    pdf_paths = []
    for i, invoice in enumerate(invoices):
        pdf_seed = _derive_seed(master_seed, f"pdf_{i}")
        pdf_path = os.path.join(output_dir, "pdfs", f"{invoice.client_id}_{invoice.invoice_number}.pdf")
        invoice.pdf_path = pdf_path # Set the path explicitly so it matches generator logic
        generate_pdf_for_invoice(invoice, seed=pdf_seed)
        pdf_paths.append(pdf_path)
        
    # 7. Generate CSVs
    csv_paths = []
    tx_by_client = defaultdict(list)
    for tx in transactions:
        tx_by_client[tx.client_id].append(tx)
        
    for client in clients:
        csv_path = os.path.join(output_dir, "csv", f"{client.id}_bank.csv")
        # Ensure dir exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        generate_bank_csv(tx_by_client[client.id], csv_path)
        csv_paths.append(csv_path)
        
    return SyntheticDataset(
        clients=clients,
        vendors=vendors,
        invoices=invoices,
        transactions=transactions,
        ground_truth=ground_truth,
        pdf_paths=pdf_paths,
        csv_paths=csv_paths
    )
