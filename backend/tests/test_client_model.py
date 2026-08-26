import pytest
import uuid
from sqlalchemy.exc import OperationalError, IntegrityError
from app.core.database import engine, Base, SessionLocal
from app.models.firm import Firm
from app.models.client import Client

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

def test_client_metadata():
    assert Client.__tablename__ == "clients"
    columns = [c.name for c in Client.__table__.columns]
    assert "id" in columns
    assert "firm_id" in columns
    assert "name" in columns
    assert "industry" in columns
    assert "currency" in columns
    assert "created_at" in columns
    
    assert "is_active" not in columns
    assert "address" not in columns
    assert "phone" not in columns
    assert "tax_id" not in columns

def test_client_construction_and_persistence(db_session):
    firm = Firm(name="Test Firm For Client")
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(firm)
    
    client = Client(
        firm_id=firm.id,
        name="Acme Corp",
        industry="Tech",
        currency="USD"
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    
    assert isinstance(client.id, uuid.UUID)
    assert client.firm_id == firm.id
    assert client.name == "Acme Corp"
    assert client.industry == "Tech"
    assert client.currency == "USD"
    assert client.created_at is not None

@pytest.mark.parametrize("missing_field", ["firm_id", "name", "currency"])
def test_client_requires_fields(db_session, missing_field):
    firm = Firm(name="Test Firm Constraints Client")
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(firm)
    
    valid_data = {
        "firm_id": firm.id,
        "name": "Jane Corp",
        "currency": "EUR"
    }
    
    valid_data.pop(missing_field)
    
    client = Client(**valid_data)
    db_session.add(client)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
        
    db_session.rollback()

def test_client_firm_relationship(db_session):
    firm = Firm(name="Rel Firm")
    client = Client(name="Rel Client", currency="GBP")
    firm.clients.append(client)
    
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(firm)
    db_session.refresh(client)
    
    assert client.firm_id == firm.id
    assert client.firm.id == firm.id
    assert len(firm.clients) == 1
    assert firm.clients[0].id == client.id
