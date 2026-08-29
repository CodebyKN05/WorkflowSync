import pytest
import uuid
import json
from fastapi.testclient import TestClient
from app.main import app
from app.models.firm import Firm
from app.models.user import User
from app.models.client import Client
from app.core.database import SessionLocal, engine, Base
from sqlalchemy.exc import OperationalError
from app.core.security import create_access_token
from app.core.config import settings

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
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()

@pytest.fixture
def test_client():
    return TestClient(app)

def test_transaction_csv_upload_authenticated_and_authorized(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test1@firm.com", password_hash="hash", firm_id=firm.id)
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add_all([user, client])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    csv_bytes = b"Date,Description,Amount,Currency\n2023-01-01,Test,-100.00,USD"

    response = test_client.post(
        "/api/v1/transactions/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client.id)},
        files={"file": ("statement.csv", csv_bytes, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "statement.csv"
    assert data["content_type"] == "text/csv"
    assert data["message"] == "Bank CSV upload accepted."

def test_transaction_csv_upload_unauthenticated(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add(client)
    db_session.commit()

    csv_bytes = b"Date,Description,Amount,Currency\n2023-01-01,Test,-100.00,USD"

    response = test_client.post(
        "/api/v1/transactions/upload",
        data={"client_id": str(client.id)},
        files={"file": ("statement.csv", csv_bytes, "text/csv")}
    )

    assert response.status_code == 401

def test_transaction_csv_upload_invalid_jwt(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add(client)
    db_session.commit()

    csv_bytes = b"Date,Description,Amount,Currency\n2023-01-01,Test,-100.00,USD"

    response = test_client.post(
        "/api/v1/transactions/upload",
        headers={"Authorization": "Bearer invalid.token.here"},
        data={"client_id": str(client.id)},
        files={"file": ("statement.csv", csv_bytes, "text/csv")}
    )

    assert response.status_code == 401

def test_transaction_csv_upload_client_not_found(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test_no_client@firm.com", password_hash="hash", firm_id=firm.id)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    csv_bytes = b"Date,Description,Amount,Currency\n2023-01-01,Test,-100.00,USD"
    random_client_id = str(uuid.uuid4())

    response = test_client.post(
        "/api/v1/transactions/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": random_client_id},
        files={"file": ("statement.csv", csv_bytes, "text/csv")}
    )

    assert response.status_code == 404
    assert "Client not found" in response.json()["detail"]

def test_transaction_csv_upload_unauthorized_firm(test_client, db_session):
    firm1 = Firm(name="Firm 1")
    firm2 = Firm(name="Firm 2")
    db_session.add_all([firm1, firm2])
    db_session.flush()

    user1 = User(name="User 1", email="user1@firm1.com", password_hash="hash", firm_id=firm1.id)
    client2 = Client(name="Client 2", industry="Tech", currency="USD", firm_id=firm2.id)
    db_session.add_all([user1, client2])
    db_session.commit()

    token = create_access_token(data={"sub": str(user1.id)})
    csv_bytes = b"Date,Description,Amount,Currency\n2023-01-01,Test,-100.00,USD"

    response = test_client.post(
        "/api/v1/transactions/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client2.id)},
        files={"file": ("statement.csv", csv_bytes, "text/csv")}
    )

    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]

def test_transaction_csv_upload_unsupported_format(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test_pdf@firm.com", password_hash="hash", firm_id=firm.id)
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add_all([user, client])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    pdf_bytes = b"%PDF-1.4..."

    response = test_client.post(
        "/api/v1/transactions/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client.id)},
        files={"file": ("statement.pdf", pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 415
    assert "Unsupported file format" in response.json()["detail"]

def test_transaction_csv_upload_oversized(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test_large@firm.com", password_hash="hash", firm_id=firm.id)
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add_all([user, client])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    large_csv_bytes = b"x" * (settings.MAX_UPLOAD_SIZE_BYTES + 1)

    response = test_client.post(
        "/api/v1/transactions/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client.id)},
        files={"file": ("large_statement.csv", large_csv_bytes, "text/csv")}
    )

    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
