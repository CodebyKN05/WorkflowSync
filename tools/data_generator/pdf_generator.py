import fitz
import os
import random
from typing import Optional
from tools.data_generator.invoice_generator import InvoiceRecord

def generate_pdf_for_invoice(invoice: InvoiceRecord, template_id: Optional[str] = None, seed: Optional[int] = None) -> None:
    """
    Generates a PDF representing an invoice and saves it to invoice.pdf_path.
    Supports multiple templates to simulate varied real-world invoice layouts.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    
    if template_id is None:
        template_id = rng.choice(["A", "B", "C"])
        
    doc = fitz.open()
    page = doc.new_page(width=595, height=842) # A4 size portrait
    
    # Ensure the parent directory exists
    pdf_dir = os.path.dirname(os.path.abspath(invoice.pdf_path))
    if pdf_dir:
        os.makedirs(pdf_dir, exist_ok=True)
        
    if template_id == "A":
        _render_template_a(page, invoice)
    elif template_id == "B":
        _render_template_b(page, invoice)
    elif template_id == "C":
        _render_template_c(page, invoice)
    else:
        raise ValueError(f"Unknown template_id: {template_id}")

    doc.save(invoice.pdf_path)
    doc.close()

def _render_template_a(page, invoice: InvoiceRecord):
    # Basic Layout
    y = 50
    margin_left = 50
    line_height = 20
    
    def add_line(text, size=12):
        nonlocal y
        page.insert_text(fitz.Point(margin_left, y), text, fontsize=size, fontname="helv")
        y += line_height
        
    add_line("INVOICE", size=24)
    y += 10
    
    add_line(f"Invoice Number: {invoice.invoice_number}")
    add_line(f"Vendor:         {invoice.vendor}")
    add_line(f"Client ID:      {invoice.client_id}")
    add_line(f"Invoice Date:   {invoice.invoice_date}")
    add_line(f"Due Date:       {invoice.due_date}")
    y += 20
    
    add_line(f"Total Amount:   {invoice.amount:.2f} {invoice.currency}", size=14)

def _render_template_b(page, invoice: InvoiceRecord):
    # Right-aligned vendor, different title, different spacing
    page.insert_text(fitz.Point(50, 50), "STATEMENT OF ACCOUNT", fontsize=20, fontname="hebo")
    
    # Vendor top right
    page.insert_text(fitz.Point(400, 50), invoice.vendor, fontsize=12, fontname="helv")
    
    page.insert_text(fitz.Point(50, 100), f"Inv #: {invoice.invoice_number}", fontsize=12, fontname="helv")
    page.insert_text(fitz.Point(50, 120), f"Billed To: {invoice.client_id}", fontsize=12, fontname="helv")
    
    page.insert_text(fitz.Point(50, 160), f"Date of Issue: {invoice.invoice_date}", fontsize=10, fontname="helv")
    page.insert_text(fitz.Point(50, 175), f"Payment Due: {invoice.due_date}", fontsize=10, fontname="helv")
    
    # Centered total
    page.insert_text(fitz.Point(200, 250), f"AMOUNT DUE: {invoice.currency} {invoice.amount:.2f}", fontsize=16, fontname="hebo")

def _render_template_c(page, invoice: InvoiceRecord):
    # Minimalist / Compact layout
    y = 60
    page.insert_text(fitz.Point(50, y), "TAX INVOICE", fontsize=18, fontname="helv")
    y += 30
    
    page.insert_text(fitz.Point(50, y), f"From: {invoice.vendor}", fontsize=11, fontname="helv")
    page.insert_text(fitz.Point(300, y), f"To: {invoice.client_id}", fontsize=11, fontname="helv")
    y += 40
    
    page.insert_text(fitz.Point(50, y), f"Reference: {invoice.invoice_number}", fontsize=11, fontname="helv")
    y += 20
    
    page.insert_text(fitz.Point(50, y), f"Date: {invoice.invoice_date}", fontsize=11, fontname="helv")
    page.insert_text(fitz.Point(300, y), f"Due: {invoice.due_date}", fontsize=11, fontname="helv")
    y += 50
    
    # Right-aligned total
    total_str = f"TOTAL: {invoice.amount:.2f} {invoice.currency}"
    # Rough right alignment
    x_pos = 500 - (len(total_str) * 7)
    page.insert_text(fitz.Point(x_pos, y), total_str, fontsize=12, fontname="helv")
