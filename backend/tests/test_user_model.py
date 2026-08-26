import pytest
import uuid
from sqlalchemy.exc import OperationalError, IntegrityError
from app.core.database import engine, Base, SessionLocal
from app.models.firm import Firm
from app.models.user import User

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

def test_user_metadata():
    assert User.__tablename__ == "users"
    columns = [c.name for c in User.__table__.columns]
    assert "id" in columns
    assert "firm_id" in columns
    assert "name" in columns
    assert "email" in columns
    assert "password_hash" in columns
    assert "created_at" in columns
    assert "role" not in columns
    assert "is_active" not in columns

def test_user_construction_and_persistence(db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(firm)
    
    user = User(
        firm_id=firm.id,
        name="John Doe",
        email="john@example.com",
        password_hash="fake_hash"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert isinstance(user.id, uuid.UUID)
    assert user.firm_id == firm.id
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.password_hash == "fake_hash"
    assert user.created_at is not None

@pytest.mark.parametrize("missing_field", ["name", "email", "password_hash", "firm_id"])
def test_user_requires_fields(db_session, missing_field):
    firm = Firm(name="Test Firm Constraints")
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(firm)
    
    valid_data = {
        "firm_id": firm.id,
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password_hash": "hash"
    }
    
    valid_data.pop(missing_field)
    
    user = User(**valid_data)
    db_session.add(user)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
        
    # Explicitly rollback the failed transaction to ensure isolation
    db_session.rollback()

def test_user_email_unique(db_session):
    firm = Firm(name="Test Firm 2")
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(firm)
    
    user1 = User(firm_id=firm.id, name="Alice", email="unique@example.com", password_hash="hash")
    user2 = User(firm_id=firm.id, name="Bob", email="unique@example.com", password_hash="hash")
    
    db_session.add(user1)
    db_session.commit()
    
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
