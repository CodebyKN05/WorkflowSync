import pytest
import uuid
from sqlalchemy.exc import OperationalError, IntegrityError
from app.core.database import engine, Base, SessionLocal
from app.models.firm import Firm

@pytest.fixture(scope="module")
def setup_database():
    """
    Follows the existing database-test strategy: skip if a real PostgreSQL
    connection is unavailable, avoiding new infrastructure setups.
    """
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

def test_firm_metadata():
    # Verify table name
    assert Firm.__tablename__ == "firms"
    # Verify columns exist in metadata
    columns = [c.name for c in Firm.__table__.columns]
    assert "id" in columns
    assert "name" in columns
    assert "created_at" in columns

def test_firm_construction_and_persistence(db_session):
    firm = Firm(name="Test Accounting Firm")
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(firm)
    
    assert firm.id is not None
    assert isinstance(firm.id, uuid.UUID)
    assert firm.name == "Test Accounting Firm"
    assert firm.created_at is not None

def test_firm_requires_name(db_session):
    firm = Firm() # Missing required name
    db_session.add(firm)
    with pytest.raises(IntegrityError):
        db_session.commit()
