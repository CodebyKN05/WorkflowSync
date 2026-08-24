import pytest
from sqlalchemy.exc import OperationalError
from app.core.database import engine, SessionLocal, Base
from app.core.config import settings

def test_database_configuration():
    # Verify settings are loaded
    assert settings.DATABASE_URL is not None
    assert "postgresql://" in settings.DATABASE_URL

    # Verify SQLAlchemy components are created
    assert engine is not None
    assert SessionLocal is not None
    assert Base is not None

def test_database_connection():
    # Attempt to connect to the database.
    # If a real PostgreSQL instance is not running locally, this will fail.
    # We catch the error to explicitly distinguish between configuration failure
    # and lack of a running local database.
    try:
        with engine.connect() as conn:
            assert conn is not None
    except OperationalError as e:
        pytest.skip(f"Could not connect to PostgreSQL. Assuming local DB is not running. Error: {e}")
