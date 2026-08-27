import pytest
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.exc import OperationalError, IntegrityError
from app.core.database import engine, Base, SessionLocal
from app.models.firm import Firm
from app.models.client import Client
from app.models.transaction import Transaction

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

def test_transaction_metadata():
    assert Transaction.__tablename__ == "transactions"
    columns = [c.name for c in Transaction.__table__.columns]
    expected_columns = [
        "id", "client_id", "transaction_date", "description", 
        "amount", "currency", "reference", "source_file", "created_at"
    ]
    for col in expected_columns:
        assert col in columns

def test_transaction_construction_and_persistence(db_session):
    firm = Firm(name="Tx Test Firm")
    db_session.add(firm)
    db_session.commit()
    
    client = Client(firm_id=firm.id, name="Tx Test Client", currency="USD")
    db_session.add(client)
    db_session.commit()
    
    transaction = Transaction(
        client_id=client.id,
        transaction_date=date(2023, 10, 1),
        description="Software Subscription",
        amount=Decimal("49.99"),
        currency="USD",
        reference="REF123",
        source_file="bank_statement.csv"
    )
    
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    assert isinstance(transaction.id, uuid.UUID)
    assert transaction.client_id == client.id
    assert transaction.transaction_date == date(2023, 10, 1)
    assert transaction.description == "Software Subscription"
    assert transaction.amount == Decimal("49.99")
    assert transaction.currency == "USD"
    assert transaction.reference == "REF123"
    assert transaction.source_file == "bank_statement.csv"
    assert transaction.created_at is not None

@pytest.mark.parametrize("missing_field", [
    "client_id", "transaction_date", "description", "amount", "currency"
])
def test_transaction_requires_fields(db_session, missing_field):
    firm = Firm(name="Constraint Test Firm")
    db_session.add(firm)
    db_session.commit()
    
    client = Client(firm_id=firm.id, name="Constraint Test Client", currency="EUR")
    db_session.add(client)
    db_session.commit()
    
    valid_data = {
        "client_id": client.id,
        "transaction_date": date(2023, 11, 1),
        "description": "Consulting Fee",
        "amount": Decimal("1000.00"),
        "currency": "EUR"
    }
    
    valid_data.pop(missing_field)
    
    transaction = Transaction(**valid_data)
    db_session.add(transaction)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
        
    db_session.rollback()

def test_transaction_client_relationship(db_session):
    firm = Firm(name="Rel Firm Tx")
    client = Client(name="Rel Client Tx", currency="GBP")
    firm.clients.append(client)
    
    transaction = Transaction(
        transaction_date=date(2023, 12, 1),
        description="Office Supplies",
        amount=Decimal("150.00"),
        currency="GBP"
    )
    client.transactions.append(transaction)
    
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(client)
    db_session.refresh(transaction)
    
    assert transaction.client_id == client.id
    assert transaction.client.id == client.id
    assert len(client.transactions) == 1  # pyright: ignore[reportArgumentType]
    assert client.transactions[0].id == transaction.id
