import os
import tempfile
import fitz
import pytest
from tools.data_generator.invoice_generator import InvoiceRecord
from tools.data_generator.pdf_generator import generate_pdf_for_invoice

@pytest.fixture
def sample_invoice():
    return InvoiceRecord(
        id="inv_123",
        client_id="client_99",
        invoice_number="INV-4005",
        vendor="Tech Solutions Inc",
        invoice_date="2026-08-01",
        due_date="2026-08-31",
        amount=1500.50,
        currency="USD",
        pdf_path="dummy_path.pdf",
        created_at="2026-08-01T00:00:00Z"
    )

def test_generate_pdf_creates_file(sample_invoice):
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, "test_invoice.pdf")
        sample_invoice.pdf_path = pdf_path
        
        generate_pdf_for_invoice(sample_invoice, template_id="A")
        
        # Verify file exists and is not empty
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0

def test_generate_pdf_content_extraction(sample_invoice):
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, "test_invoice_2.pdf")
        sample_invoice.pdf_path = pdf_path
        
        generate_pdf_for_invoice(sample_invoice, template_id="A")
        
        # Extract text to verify contents
        doc = fitz.open(pdf_path)
        text = doc[0].get_text()
        doc.close()
        
        assert sample_invoice.invoice_number in text
        assert sample_invoice.vendor in text
        assert sample_invoice.client_id in text
        assert sample_invoice.invoice_date in text
        assert sample_invoice.due_date in text
        assert f"{sample_invoice.amount:.2f}" in text
        assert sample_invoice.currency in text

def test_multiple_templates_generate_different_layouts(sample_invoice):
    with tempfile.TemporaryDirectory() as temp_dir:
        paths = []
        texts = []
        for template in ["A", "B", "C"]:
            pdf_path = os.path.join(temp_dir, f"test_invoice_{template}.pdf")
            sample_invoice.pdf_path = pdf_path
            paths.append(pdf_path)
            generate_pdf_for_invoice(sample_invoice, template_id=template)
            
            doc = fitz.open(pdf_path)
            texts.append(doc[0].get_text())
            doc.close()
            
        assert len(paths) == 3
        # Assert texts contain different template-specific headers/labels
        assert "INVOICE" in texts[0]
        assert "STATEMENT OF ACCOUNT" in texts[1]
        assert "TAX INVOICE" in texts[2]
        
        # Verify all templates contain the core invoice data
        for text in texts:
            assert sample_invoice.invoice_number in text
            assert sample_invoice.vendor in text
            assert f"{sample_invoice.amount:.2f}" in text

def test_deterministic_template_selection(sample_invoice):
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path1 = os.path.join(temp_dir, "test1.pdf")
        pdf_path2 = os.path.join(temp_dir, "test2.pdf")
        
        sample_invoice.pdf_path = pdf_path1
        generate_pdf_for_invoice(sample_invoice, seed=42)
        doc = fitz.open(pdf_path1)
        text1 = doc[0].get_text()
        doc.close()
        
        sample_invoice.pdf_path = pdf_path2
        generate_pdf_for_invoice(sample_invoice, seed=42)
        doc = fitz.open(pdf_path2)
        text2 = doc[0].get_text()
        doc.close()
        
        # With the same seed, the same template should be randomly selected and yield the same text
        assert text1 == text2

def test_multiple_invoices_produce_separate_files(sample_invoice):
    with tempfile.TemporaryDirectory() as temp_dir:
        inv1 = sample_invoice
        inv1.pdf_path = os.path.join(temp_dir, "inv1.pdf")
        
        # Create a copy with different values
        inv2_dict = sample_invoice.to_dict()
        inv2_dict["invoice_number"] = "INV-9999"
        inv2_dict["pdf_path"] = os.path.join(temp_dir, "inv2.pdf")
        inv2 = InvoiceRecord(**inv2_dict)
        
        generate_pdf_for_invoice(inv1, template_id="A")
        generate_pdf_for_invoice(inv2, template_id="A")
        
        assert os.path.exists(inv1.pdf_path)
        assert os.path.exists(inv2.pdf_path)
        
        # Verify they are actually different
        doc1 = fitz.open(inv1.pdf_path)
        text1 = doc1[0].get_text()
        doc1.close()
        
        doc2 = fitz.open(inv2.pdf_path)
        text2 = doc2[0].get_text()
        doc2.close()
        
        assert "INV-4005" in text1
        assert "INV-9999" not in text1
        assert "INV-9999" in text2
        assert "INV-4005" not in text2
