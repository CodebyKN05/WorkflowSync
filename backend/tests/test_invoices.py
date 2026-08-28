import pytest
import uuid
import json
import fitz
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
        # Clean up database
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()

@pytest.fixture
def test_client():
    return TestClient(app)

def create_pdf_with_text(text_list: list[str] = None) -> bytes:
    doc = fitz.open()
    if not text_list:
        doc.new_page()
    else:
        for text in text_list:
            page = doc.new_page()
            if text:
                page.insert_text(fitz.Point(50, 50), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

def test_invoice_upload_unauthenticated(test_client):
    response = test_client.post(
        "/api/v1/invoices/upload",
        data={"client_id": str(uuid.uuid4())},
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    )
    assert response.status_code == 401

def test_invoice_upload_invalid_jwt(test_client):
    response = test_client.post(
        "/api/v1/invoices/upload",
        headers={"Authorization": "Bearer invalid_token"},
        data={"client_id": str(uuid.uuid4())},
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    )
    assert response.status_code == 401

def test_invoice_upload_authenticated_and_authorized(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test@firm.com", password_hash="hash", firm_id=firm.id)
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add_all([user, client])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    valid_pdf_bytes = create_pdf_with_text(["Test Invoice Data"])

    response = test_client.post(
        "/api/v1/invoices/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client.id)},
        files={"file": ("invoice123.pdf", valid_pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "invoice123.pdf"
    assert data["content_type"] == "application/pdf"
    assert data["message"] == "Invoice upload and extraction successful"
    assert "Test Invoice Data" in data["extracted_text"]

def test_invoice_upload_unauthorized_firm(test_client, db_session):
    firm1 = Firm(name="My Firm")
    firm2 = Firm(name="Other Firm")
    db_session.add_all([firm1, firm2])
    db_session.flush()

    user = User(name="Test User", email="test2@firm.com", password_hash="hash", firm_id=firm1.id)
    client2 = Client(name="Other Client", industry="Tech", currency="USD", firm_id=firm2.id)
    db_session.add_all([user, client2])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    valid_pdf_bytes = create_pdf_with_text()

    response = test_client.post(
        "/api/v1/invoices/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client2.id)},
        files={"file": ("invoice123.pdf", valid_pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]

def test_invoice_upload_client_not_found(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()
    user = User(name="Test User", email="test3@firm.com", password_hash="hash", firm_id=firm.id)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    valid_pdf_bytes = create_pdf_with_text()

    response = test_client.post(
        "/api/v1/invoices/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(uuid.uuid4())},
        files={"file": ("invoice123.pdf", valid_pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_invoice_upload_unsupported_format(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test_unsupported@firm.com", password_hash="hash", firm_id=firm.id)
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add_all([user, client])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    response = test_client.post(
        "/api/v1/invoices/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client.id)},
        files={"file": ("invoice123.txt", b"this is text not a pdf", "text/plain")}
    )

    assert response.status_code == 415
    assert "Unsupported file format" in response.json()["detail"]

def test_invoice_upload_corrupt_pdf(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test_corrupt@firm.com", password_hash="hash", firm_id=firm.id)
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add_all([user, client])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    
    # Has %PDF- but is corrupt
    corrupt_pdf_bytes = b"%PDF-1.4\n% this is corrupt\nand will fail fitz open"

    response = test_client.post(
        "/api/v1/invoices/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client.id)},
        files={"file": ("invoice123.pdf", corrupt_pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 400
    assert "Corrupt or invalid PDF" in response.json()["detail"]

def test_invoice_upload_oversized(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test_oversized@firm.com", password_hash="hash", firm_id=firm.id)
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add_all([user, client])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    
    oversized_bytes = b"%PDF-1.4\n" + (b"0" * settings.MAX_UPLOAD_SIZE_BYTES)

    response = test_client.post(
        "/api/v1/invoices/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client.id)},
        files={"file": ("invoice123.pdf", oversized_bytes, "application/pdf")}
    )

    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]

def test_invoice_upload_multi_page_text(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test_multi@firm.com", password_hash="hash", firm_id=firm.id)
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add_all([user, client])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    valid_pdf_bytes = create_pdf_with_text(["Page 1 Text", "Page 2 Text", "Page 3 Text"])

    response = test_client.post(
        "/api/v1/invoices/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client.id)},
        files={"file": ("invoice_multi.pdf", valid_pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "Page 1 Text" in data["extracted_text"]
    assert "Page 2 Text" in data["extracted_text"]
    assert "Page 3 Text" in data["extracted_text"]

def test_invoice_upload_empty_pdf(test_client, db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test User", email="test_empty@firm.com", password_hash="hash", firm_id=firm.id)
    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add_all([user, client])
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    valid_pdf_bytes = create_pdf_with_text() # Creates an empty page

    response = test_client.post(
        "/api/v1/invoices/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"client_id": str(client.id)},
        files={"file": ("invoice_empty.pdf", valid_pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["extracted_text"] == ""
