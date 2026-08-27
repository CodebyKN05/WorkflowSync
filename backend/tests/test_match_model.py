import pytest
import uuid
from decimal import Decimal
from datetime import date
from typing import cast
from sqlalchemy.exc import OperationalError, IntegrityError
from app.core.database import engine, Base, SessionLocal
from app.models.firm import Firm
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.transaction import Transaction
from app.models.match import Match

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

def test_match_metadata():
    assert Match.__tablename__ == "matches"
    
    columns = {c.name: c for c in Match.__table__.columns}
    assert "id" in columns
    assert "invoice_id" in columns
    assert "transaction_id" in columns
    assert "score" in columns
    assert "status" in columns
    assert "reason" in columns
    assert "created_at" in columns
    assert "updated_at" in columns
    assert "matched_at" not in columns

def test_match_construction_and_persistence(db_session):
    firm = Firm(name="Match Firm")
    client = Client(name="Match Client", currency="GBP")
    firm.clients.append(client)
    
    invoice = Invoice(
        invoice_number="INV-MATCH-01",
        vendor="Vendor 1",
        invoice_date=date(2023, 1, 1),
        due_date=date(2023, 1, 31),
        amount=Decimal("100.00"),
        currency="GBP"
    )
    client.invoices.append(invoice)
    
    transaction = Transaction(
        transaction_date=date(2023, 1, 15),
        description="Payment to Vendor 1",
        amount=Decimal("-100.00"),
        currency="GBP"
    )
    client.transactions.append(transaction)
    
    db_session.add(firm)
    db_session.commit()
    
    match = Match(
        invoice_id=invoice.id,
        transaction_id=transaction.id,
        score=Decimal("95.50"),
        status="PROPOSED",
        reason="Amounts match perfectly"
    )
    
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    
    assert isinstance(match.id, uuid.UUID)
    assert match.invoice_id == invoice.id
    assert match.transaction_id == transaction.id
    assert match.score == Decimal("95.50")
    assert match.status == "PROPOSED"
    assert match.reason == "Amounts match perfectly"
    assert match.created_at is not None
    assert match.updated_at is not None
    assert match.invoice.id == invoice.id
    assert match.transaction.id == transaction.id

@pytest.mark.parametrize("missing_field", [
    "invoice_id",
    "transaction_id",
    "score",
    "status",
    "reason"
])
def test_match_requires_fields(db_session, missing_field):
    firm = Firm(name=f"Match Missing Firm {missing_field}")
    client = Client(name=f"Match Missing Client {missing_field}", currency="GBP")
    firm.clients.append(client)
    
    invoice = Invoice(
        invoice_number=f"INV-MISSING-{missing_field}",
        vendor="Vendor 1",
        invoice_date=date(2023, 1, 1),
        due_date=date(2023, 1, 31),
        amount=Decimal("100.00"),
        currency="GBP"
    )
    client.invoices.append(invoice)
    
    transaction = Transaction(
        transaction_date=date(2023, 1, 15),
        description="Payment to Vendor 1",
        amount=Decimal("-100.00"),
        currency="GBP"
    )
    client.transactions.append(transaction)
    
    db_session.add(firm)
    db_session.commit()
    
    match_data = {
        "invoice_id": invoice.id,
        "transaction_id": transaction.id,
        "score": Decimal("95.50"),
        "status": "PROPOSED",
        "reason": "Amounts match perfectly"
    }
    
    del match_data[missing_field]
    
    match = Match(**match_data)
    db_session.add(match)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
        
    db_session.rollback()

def test_match_invoice_relationship(db_session):
    firm = Firm(name="Match Rel Firm")
    client = Client(name="Match Rel Client", currency="GBP")
    firm.clients.append(client)
    
    invoice = Invoice(
        invoice_number="INV-REL-01",
        vendor="Vendor 1",
        invoice_date=date(2023, 1, 1),
        due_date=date(2023, 1, 31),
        amount=Decimal("100.00"),
        currency="GBP"
    )
    client.invoices.append(invoice)
    
    transaction = Transaction(
        transaction_date=date(2023, 1, 15),
        description="Payment to Vendor 1",
        amount=Decimal("-100.00"),
        currency="GBP"
    )
    client.transactions.append(transaction)
    
    match = Match(
        transaction_id=transaction.id,
        score=Decimal("100.00"),
        status="CONFIRMED",
        reason="Manual match"
    )
    invoice.matches.append(match)
    
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(invoice)
    db_session.refresh(match)
    
    assert match.invoice_id == invoice.id
    assert match.invoice.id == invoice.id
    assert len(cast(list[Match], invoice.matches)) == 1
    assert invoice.matches[0].id == match.id

def test_match_transaction_relationship(db_session):
    firm = Firm(name="Match Rel Tx Firm")
    client = Client(name="Match Rel Tx Client", currency="GBP")
    firm.clients.append(client)
    
    invoice = Invoice(
        invoice_number="INV-REL-02",
        vendor="Vendor 2",
        invoice_date=date(2023, 1, 1),
        due_date=date(2023, 1, 31),
        amount=Decimal("200.00"),
        currency="GBP"
    )
    client.invoices.append(invoice)
    
    transaction = Transaction(
        transaction_date=date(2023, 1, 15),
        description="Payment to Vendor 2",
        amount=Decimal("-200.00"),
        currency="GBP"
    )
    client.transactions.append(transaction)
    
    match = Match(
        invoice_id=invoice.id,
        score=Decimal("100.00"),
        status="CONFIRMED",
        reason="Manual match"
    )
    transaction.matches.append(match)
    
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(transaction)
    db_session.refresh(match)
    
    assert match.transaction_id == transaction.id
    assert match.transaction.id == transaction.id
    assert len(cast(list[Match], transaction.matches)) == 1
    assert transaction.matches[0].id == match.id
