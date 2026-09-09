import pytest
import uuid
from datetime import date
from typing import cast
from sqlalchemy.exc import OperationalError, IntegrityError
from app.core.database import engine, Base, SessionLocal
from app.models.firm import Firm
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.transaction import Transaction
from app.models.exception import ReconciliationException

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

def test_exception_metadata():
    assert ReconciliationException.__tablename__ == "exceptions"
    
    columns = {c.name: c for c in ReconciliationException.__table__.columns}
    assert "id" in columns
    assert "invoice_id" in columns
    assert "transaction_id" in columns
    assert "type" in columns
    assert "status" in columns
    assert "created_at" in columns
    assert "reconciliation_run_id" in columns
    assert "client_id" not in columns
    
    assert columns["invoice_id"].nullable is True
    assert columns["transaction_id"].nullable is True
    assert columns["type"].nullable is False
    assert columns["description"].nullable is False
    assert columns["status"].nullable is False

def create_base_entities(db_session):
    firm = Firm(name="Exception Firm")
    client = Client(name="Exception Client", currency="USD")
    firm.clients.append(client)
    db_session.add(firm)
    db_session.flush()

    invoice = Invoice(
        client_id=client.id,
        invoice_number="EXC-INV-01",
        vendor="Test Vendor",
        invoice_date=date(2026, 8, 1),
        due_date=date(2026, 8, 30),
        amount=100.00,
        currency="USD"
    )
    transaction = Transaction(
        client_id=client.id,
        transaction_date=date(2026, 8, 15),
        description="Test Payment",
        amount=-100.00,
        currency="USD"
    )
    from app.models.reconciliation_run import ReconciliationRun
    from datetime import datetime, timezone
    run = ReconciliationRun(
        client_id=client.id,
        status="completed",
        started_at=datetime.now(timezone.utc)
    )
    db_session.add(invoice)
    db_session.add(transaction)
    db_session.add(run)
    db_session.flush()
    return invoice, transaction, run

def test_exception_invoice_only_persistence(db_session):
    invoice, _, run = create_base_entities(db_session)
    
    exc = ReconciliationException(
        reconciliation_run_id=run.id,
        invoice_id=invoice.id,
        type="MISSING_PAYMENT",
        description="Invoice has no matching payment",
        status="OPEN"
    )
    db_session.add(exc)
    db_session.commit()
    db_session.refresh(exc)
    
    assert exc.id is not None
    assert exc.invoice_id == invoice.id
    assert exc.transaction_id is None
    assert exc.type == "MISSING_PAYMENT"

def test_exception_transaction_only_persistence(db_session):
    _, transaction, run = create_base_entities(db_session)
    
    exc = ReconciliationException(
        reconciliation_run_id=run.id,
        transaction_id=transaction.id,
        type="UNRELATED_TRANSACTION",
        description="Transaction has no matching invoice",
        status="OPEN"
    )
    db_session.add(exc)
    db_session.commit()
    db_session.refresh(exc)
    
    assert exc.id is not None
    assert exc.invoice_id is None
    assert exc.transaction_id == transaction.id
    assert exc.type == "UNRELATED_TRANSACTION"

def test_exception_both_references(db_session):
    invoice, transaction, run = create_base_entities(db_session)
    
    exc = ReconciliationException(
        reconciliation_run_id=run.id,
        invoice_id=invoice.id,
        transaction_id=transaction.id,
        type="AMOUNT_MISMATCH",
        description="Amounts differ slightly",
        status="REVIEW"
    )
    db_session.add(exc)
    db_session.commit()
    db_session.refresh(exc)
    
    assert exc.invoice_id == invoice.id
    assert exc.transaction_id == transaction.id

@pytest.mark.parametrize("field, value", [
    ("type", None),
    ("description", None),
    ("status", None),
])
def test_exception_requires_fields(db_session, field, value):
    invoice, _, run = create_base_entities(db_session)
    
    valid_data = {
        "reconciliation_run_id": run.id,
        "invoice_id": invoice.id,
        "type": "MISSING_PAYMENT",
        "description": "Invoice has no matching payment",
        "status": "OPEN"
    }
    valid_data[field] = value
    
    exc = ReconciliationException(**valid_data)
    db_session.add(exc)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_exception_invoice_relationship(db_session):
    invoice, _, run = create_base_entities(db_session)
    
    exc = ReconciliationException(
        reconciliation_run_id=run.id,
        invoice_id=invoice.id,
        type="MISSING_PAYMENT",
        description="Invoice has no matching payment",
        status="OPEN"
    )
    db_session.add(exc)
    db_session.commit()
    
    assert len(cast(list[ReconciliationException], invoice.exceptions)) == 1
    assert invoice.exceptions[0].type == "MISSING_PAYMENT"
    assert exc.invoice.id == invoice.id

def test_exception_transaction_relationship(db_session):
    _, transaction, run = create_base_entities(db_session)
    
    exc = ReconciliationException(
        reconciliation_run_id=run.id,
        transaction_id=transaction.id,
        type="UNRELATED_TRANSACTION",
        description="Transaction has no matching invoice",
        status="OPEN"
    )
    db_session.add(exc)
    db_session.commit()
    
    assert len(cast(list[ReconciliationException], transaction.exceptions)) == 1
    assert transaction.exceptions[0].type == "UNRELATED_TRANSACTION"
    assert exc.transaction.id == transaction.id

def test_exception_run_relationship(db_session):
    _, _, run = create_base_entities(db_session)
    
    exc = ReconciliationException(
        reconciliation_run_id=run.id,
        type="MISSING_DATA",
        description="Missing data",
        status="OPEN"
    )
    db_session.add(exc)
    db_session.commit()
    
    assert len(cast(list[ReconciliationException], run.exceptions)) == 1
    assert run.exceptions[0].type == "MISSING_DATA"
    assert exc.reconciliation_run.id == run.id
