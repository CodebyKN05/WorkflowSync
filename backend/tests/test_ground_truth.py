import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import OperationalError
from app.core.database import engine, Base, SessionLocal

from app.models.firm import Firm
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.transaction import Transaction
from app.models.match import Match
from app.models.reconciliation_run import ReconciliationRun
from app.services.reconciliation_engine import run_reconciliation

@pytest.fixture(scope="module")
def setup_database():
    try:
        with engine.connect() as conn:
            pass
    except OperationalError:
        pytest.skip("Could not connect to the database")
    
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_database):
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def test_client(db_session):
    firm = Firm(name="Ground Truth Firm")
    db_session.add(firm)
    db_session.flush()

    client = Client(name="Ground Truth Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add(client)
    db_session.commit()
    return client

def test_ground_truth_exact_match(db_session, test_client):
    invoice = Invoice(client_id=test_client.id, invoice_number="INV-EXACT", vendor="Exact Vendor", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("100.00"), currency="USD")
    transaction = Transaction(client_id=test_client.id, transaction_date=date(2023, 1, 1), description="Exact Vendor", amount=Decimal("-100.00"), currency="USD", reference="INV-EXACT")
    
    db_session.add_all([invoice, transaction])
    db_session.flush()

    run = run_reconciliation(db_session, test_client.id, [invoice], [transaction])

    assert run.matched_count == 1  # type: ignore
    assert run.review_count == 0  # type: ignore
    assert run.unmatched_count == 0  # type: ignore
    assert run.duplicate_count == 0  # type: ignore

    match = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).first()
    assert match is not None
    assert match.status == "MATCHED"  # type: ignore
    assert match.score == Decimal("100.00")  # type: ignore
    assert "Exact match" in match.reason  # type: ignore

def test_ground_truth_vendor_variation(db_session, test_client):
    invoice = Invoice(client_id=test_client.id, invoice_number="INV-VEND", vendor="Amazon Web Services", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("150.00"), currency="USD")
    # Substring variation that rapidfuzz matches well
    transaction = Transaction(client_id=test_client.id, transaction_date=date(2023, 1, 1), description="AWS PAYMENT 123", amount=Decimal("-150.00"), currency="USD")
    
    db_session.add_all([invoice, transaction])
    db_session.flush()

    run = run_reconciliation(db_session, test_client.id, [invoice], [transaction])

    match = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).first()
    assert match is not None
    assert match.status in ["MATCHED", "NEEDS_REVIEW"]  # type: ignore (Depends on rapidfuzz score)

def test_ground_truth_amount_mismatch(db_session, test_client):
    invoice = Invoice(client_id=test_client.id, invoice_number="INV-AMT", vendor="Amount Vendor", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("100.00"), currency="USD")
    transaction = Transaction(client_id=test_client.id, transaction_date=date(2023, 1, 1), description="Amount Vendor", amount=Decimal("-90.00"), currency="USD")
    
    db_session.add_all([invoice, transaction])
    db_session.flush()

    run = run_reconciliation(db_session, test_client.id, [invoice], [transaction])

    match = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).first()
    assert match is not None
    assert match.score < Decimal("100.00")  # type: ignore
    assert "10.00 difference" in match.reason  # type: ignore

def test_ground_truth_missing_payment(db_session, test_client):
    invoice = Invoice(client_id=test_client.id, invoice_number="INV-MISSING", vendor="Missing Vendor", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("100.00"), currency="USD")
    # NO transaction
    
    db_session.add(invoice)
    db_session.flush()

    run = run_reconciliation(db_session, test_client.id, [invoice], [])

    assert run.matched_count == 0  # type: ignore
    assert run.unmatched_count == 1  # type: ignore
    
    matches = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).all()
    assert len(matches) == 0

def test_ground_truth_no_candidate(db_session, test_client):
    invoice = Invoice(client_id=test_client.id, invoice_number="INV-NOCAND", vendor="NoCand Vendor", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("100.00"), currency="USD")
    # Completely unrelated transaction (wrong currency, so candidate generator ignores it)
    transaction = Transaction(client_id=test_client.id, transaction_date=date(2023, 5, 1), description="Totally Unrelated", amount=Decimal("-500.00"), currency="EUR")
    
    db_session.add_all([invoice, transaction])
    db_session.flush()

    run = run_reconciliation(db_session, test_client.id, [invoice], [transaction])

    assert run.unmatched_count == 1  # type: ignore
    
    matches = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).all()
    assert len(matches) == 0

def test_ground_truth_duplicate_payment(db_session, test_client):
    invoice = Invoice(client_id=test_client.id, invoice_number="INV-DUP", vendor="Dup Vendor", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("100.00"), currency="USD")
    
    # TWO perfect matches
    transaction1 = Transaction(client_id=test_client.id, transaction_date=date(2023, 1, 1), description="Dup Vendor", amount=Decimal("-100.00"), currency="USD")
    transaction2 = Transaction(client_id=test_client.id, transaction_date=date(2023, 1, 1), description="Dup Vendor", amount=Decimal("-100.00"), currency="USD")
    
    db_session.add_all([invoice, transaction1, transaction2])
    db_session.flush()

    run = run_reconciliation(db_session, test_client.id, [invoice], [transaction1, transaction2])

    assert run.duplicate_count == 2  # type: ignore
    
    matches = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).all()
    assert len(matches) == 2
    assert matches[0].status == "DUPLICATE"  # type: ignore
    assert matches[1].status == "DUPLICATE"  # type: ignore

def test_ground_truth_date_mismatch(db_session, test_client):
    invoice = Invoice(client_id=test_client.id, invoice_number="INV-DATE", vendor="Date Vendor", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("100.00"), currency="USD")
    # Date 10 days apart
    transaction = Transaction(client_id=test_client.id, transaction_date=date(2023, 1, 11), description="Date Vendor", amount=Decimal("-100.00"), currency="USD")
    
    db_session.add_all([invoice, transaction])
    db_session.flush()

    run = run_reconciliation(db_session, test_client.id, [invoice], [transaction])

    match = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).first()
    assert match is not None
    assert match.score < Decimal("100.00")  # type: ignore
    assert "10 days apart" in match.reason  # type: ignore
