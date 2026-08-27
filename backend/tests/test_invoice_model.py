import pytest
import uuid
from typing import cast
from decimal import Decimal
from datetime import date
from sqlalchemy.exc import OperationalError, IntegrityError
from app.core.database import engine, Base, SessionLocal
from app.models.firm import Firm
from app.models.client import Client
from app.models.invoice import Invoice

@pytest.fixture(scope="module")
def setup_database():
    try:
        with engine.connect() as conn:
            pass
    except OperationalError as e:
        pytest.skip(f"Could not connect to PostgreSQL. Assuming local DB is not running. Error: {e}")
        
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_database):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def test_invoice_metadata():
    assert Invoice.__tablename__ == "invoices"
    columns = [c.name for c in Invoice.__table__.columns]
    expected_columns = [
        "id", "client_id", "invoice_number", "vendor", "invoice_date", 
        "due_date", "amount", "currency", "pdf_path", "status", "created_at"
    ]
    for col in expected_columns:
        assert col in columns

def test_invoice_construction_and_persistence(db_session):
    firm = Firm(name="Invoice Test Firm")
    db_session.add(firm)
    db_session.commit()
    
    client = Client(firm_id=firm.id, name="Invoice Test Client", currency="USD")
    db_session.add(client)
    db_session.commit()
    
    invoice = Invoice(
        client_id=client.id,
        invoice_number="INV-001",
        vendor="Tech Vendor Inc",
        invoice_date=date(2023, 10, 1),
        due_date=date(2023, 10, 31),
        amount=Decimal("1500.50"),
        currency="USD"
    )
    
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    
    assert isinstance(invoice.id, uuid.UUID)
    assert invoice.client_id == client.id
    assert invoice.invoice_number == "INV-001"
    assert invoice.vendor == "Tech Vendor Inc"
    assert invoice.invoice_date == date(2023, 10, 1)
    assert invoice.due_date == date(2023, 10, 31)
    assert invoice.amount == Decimal("1500.50")
    assert invoice.currency == "USD"
    assert invoice.pdf_path is None
    assert invoice.status == "pending"
    assert invoice.created_at is not None

@pytest.mark.parametrize("missing_field", [
    "client_id", "invoice_number", "vendor", "invoice_date", 
    "due_date", "amount", "currency"
])
def test_invoice_requires_fields(db_session, missing_field):
    firm = Firm(name="Constraint Test Firm")
    db_session.add(firm)
    db_session.commit()
    
    client = Client(firm_id=firm.id, name="Constraint Test Client", currency="EUR")
    db_session.add(client)
    db_session.commit()
    
    valid_data = {
        "client_id": client.id,
        "invoice_number": "INV-REQ",
        "vendor": "Vendor",
        "invoice_date": date(2023, 11, 1),
        "due_date": date(2023, 11, 30),
        "amount": Decimal("100.00"),
        "currency": "EUR"
    }
    
    valid_data.pop(missing_field)
    
    invoice = Invoice(**valid_data)
    db_session.add(invoice)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
        
    db_session.rollback()

def test_invoice_client_relationship(db_session):
    firm = Firm(name="Rel Firm Invoice")
    client = Client(name="Rel Client Invoice", currency="GBP")
    firm.clients.append(client)
    
    invoice = Invoice(
        invoice_number="INV-REL",
        vendor="Rel Vendor",
        invoice_date=date(2023, 12, 1),
        due_date=date(2023, 12, 31),
        amount=Decimal("200.00"),
        currency="GBP"
    )
    client.invoices.append(invoice)
    
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(client)
    db_session.refresh(invoice)
    
    assert invoice.client_id == client.id
    assert invoice.client.id == client.id
    assert len(cast(list[Invoice], client.invoices)) == 1
    assert client.invoices[0].id == invoice.id
