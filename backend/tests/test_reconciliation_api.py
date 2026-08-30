import pytest
from datetime import date
from decimal import Decimal
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.firm import Firm
from app.models.user import User
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.transaction import Transaction
from app.models.reconciliation_run import ReconciliationRun
from app.models.match import Match
from app.core.security import create_access_token

from app.main import app
from app.core.database import SessionLocal, engine, Base
from sqlalchemy.exc import OperationalError

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

@pytest.fixture
def auth_headers(db_session: Session):
    firm = Firm(name="API Test Firm")
    db_session.add(firm)
    db_session.flush()

    user = User(name="Test API User", email="apitester@firm.com", password_hash="hash", firm_id=firm.id)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}, user

@pytest.fixture
def api_base_data(db_session: Session, auth_headers):
    _, user = auth_headers
    
    client = Client(name="API Client", industry="Tech", currency="USD", firm_id=user.firm_id)
    db_session.add(client)
    db_session.flush()

    run = ReconciliationRun(
        client_id=client.id,
        matched_count=1,
        review_count=1,
        unmatched_count=0,
        duplicate_count=1,
        status="completed"
    )
    db_session.add(run)
    db_session.flush()
    
    invoice = Invoice(client_id=client.id, invoice_number="INV-API", vendor="API Vendor", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("100.00"), currency="USD")
    transaction = Transaction(client_id=client.id, transaction_date=date(2023, 1, 5), description="API Vendor", amount=Decimal("-100.00"), currency="USD", reference="REF-123")
    transaction2 = Transaction(client_id=client.id, transaction_date=date(2023, 1, 5), description="API Vendor 2", amount=Decimal("-100.00"), currency="USD", reference="REF-456")
    
    db_session.add_all([invoice, transaction, transaction2])
    db_session.flush()
    
    # Matched
    match1 = Match(
        reconciliation_run_id=run.id,
        invoice_id=invoice.id,
        transaction_id=transaction.id,
        score=Decimal("95.00"),
        status="MATCHED",
        reason="Good"
    )
    
    # Needs Review
    invoice_review = Invoice(client_id=client.id, invoice_number="INV-REV", vendor="Review Vendor", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("200.00"), currency="USD")
    transaction_review = Transaction(client_id=client.id, transaction_date=date(2023, 1, 5), description="Review Vendor", amount=Decimal("-200.00"), currency="USD", reference="REF-REV")
    db_session.add_all([invoice_review, transaction_review])
    db_session.flush()

    match2 = Match(
        reconciliation_run_id=run.id,
        invoice_id=invoice_review.id,
        transaction_id=transaction_review.id,
        score=Decimal("75.00"),
        status="NEEDS_REVIEW",
        reason="Check vendor"
    )
    
    # Duplicate (2 candidates for the same invoice)
    match3 = Match(
        reconciliation_run_id=run.id,
        invoice_id=invoice.id,
        transaction_id=transaction.id,
        score=Decimal("100.00"),
        status="DUPLICATE",
        reason="Duplicate candidate 1"
    )
    
    match4 = Match(
        reconciliation_run_id=run.id,
        invoice_id=invoice.id,
        transaction_id=transaction2.id,
        score=Decimal("100.00"),
        status="DUPLICATE",
        reason="Duplicate candidate 2"
    )
    
    db_session.add_all([match1, match2, match3, match4])
    db_session.commit()
    
    return {
        "client": client,
        "run": run,
        "invoice": invoice,
        "transaction": transaction,
        "match_matched": match1,
        "match_review": match2,
        "match_duplicate": match3
    }


def test_get_review_queue_success(test_client: TestClient, api_base_data: dict, auth_headers: tuple):
    headers, _ = auth_headers
    run = api_base_data["run"]
    
    response = test_client.get(f"/api/v1/reconciliation/runs/{run.id}/queue", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3  # 1 NEEDS_REVIEW and 2 DUPLICATE
    
    statuses = [m["status"] for m in data]
    assert "NEEDS_REVIEW" in statuses
    assert "DUPLICATE" in statuses
    assert "MATCHED" not in statuses
    
    # Verify explicitly required fields for Candidate Display
    review_match = next(m for m in data if m["status"] == "NEEDS_REVIEW")
    assert review_match["score"] == "75.00"
    assert review_match["reason"] == "Check vendor"
    assert review_match["invoice"]["invoice_number"] == "INV-REV"
    assert review_match["invoice"]["amount"] == "200.00"
    assert review_match["transaction"]["description"] == "Review Vendor"
    assert review_match["transaction"]["amount"] == "-200.00"
    assert review_match["transaction"]["reference"] == "REF-REV"
    
    # Verify multiple candidates for the same invoice are correctly represented
    duplicate_matches = [m for m in data if m["status"] == "DUPLICATE"]
    assert len(duplicate_matches) == 2
    
    # Both duplicates should have the same invoice ID and number
    assert duplicate_matches[0]["invoice"]["id"] == duplicate_matches[1]["invoice"]["id"]
    assert duplicate_matches[0]["invoice"]["invoice_number"] == "INV-API"
    
    # But they should have different transaction references
    refs = {m["transaction"]["reference"] for m in duplicate_matches}
    assert "REF-123" in refs
    assert "REF-456" in refs


def test_get_review_queue_not_found(test_client: TestClient, auth_headers: tuple):
    headers, _ = auth_headers
    random_id = str(uuid.uuid4())
    
    response = test_client.get(f"/api/v1/reconciliation/runs/{random_id}/queue", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Reconciliation run not found"


def test_get_review_queue_cross_firm_isolation(test_client: TestClient, db_session: Session, api_base_data: dict):
    # Create a new user in a different firm
    firm2 = Firm(name="Other Firm")
    db_session.add(firm2)
    db_session.flush()

    user2 = User(name="Other User", email="other@firm.com", password_hash="hash", firm_id=firm2.id)
    db_session.add(user2)
    db_session.commit()

    token2 = create_access_token(data={"sub": str(user2.id)})
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    run = api_base_data["run"]
    
    response = test_client.get(f"/api/v1/reconciliation/runs/{run.id}/queue", headers=headers2)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this run"


def test_get_review_queue_unauthenticated(test_client: TestClient, api_base_data: dict):
    run = api_base_data["run"]
    response = test_client.get(f"/api/v1/reconciliation/runs/{run.id}/queue")
    assert response.status_code == 401

def test_confirm_match_success(test_client: TestClient, db_session: Session, api_base_data: dict, auth_headers: tuple):
    headers, _ = auth_headers
    run = api_base_data["run"]
    match_review = api_base_data["match_review"]
    
    # Store initial counts
    initial_matched = run.matched_count
    initial_review = run.review_count
    
    response = test_client.post(f"/api/v1/reconciliation/matches/{match_review.id}/confirm", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "MATCHED"
    assert data["id"] == str(match_review.id)
    
    # Verify DB update and counts
    db_session.refresh(match_review)
    db_session.refresh(run)
    assert match_review.status == "MATCHED"
    assert run.matched_count == initial_matched + 1
    assert run.review_count == initial_review - 1

def test_confirm_match_duplicate_and_siblings_unchanged(test_client: TestClient, db_session: Session, api_base_data: dict, auth_headers: tuple):
    headers, _ = auth_headers
    run = api_base_data["run"]
    match_duplicate = api_base_data["match_duplicate"] # This is match3
    
    # Get sibling candidate (match4)
    sibling = db_session.query(Match).filter(
        Match.invoice_id == match_duplicate.invoice_id,
        Match.id != match_duplicate.id,
        Match.status == "DUPLICATE"
    ).first()
    
    assert sibling is not None
    
    initial_matched = run.matched_count
    initial_duplicate = run.duplicate_count
    
    response = test_client.post(f"/api/v1/reconciliation/matches/{match_duplicate.id}/confirm", headers=headers)
    assert response.status_code == 200
    
    # Verify DB update and counts
    db_session.refresh(match_duplicate)
    db_session.refresh(sibling)
    db_session.refresh(run)
    
    assert match_duplicate.status == "MATCHED"
    assert sibling.status == "DUPLICATE" # Sibling unchanged
    assert run.matched_count == initial_matched + 1
    assert run.duplicate_count == initial_duplicate - 1

def test_confirm_match_idempotent(test_client: TestClient, db_session: Session, api_base_data: dict, auth_headers: tuple):
    headers, _ = auth_headers
    run = api_base_data["run"]
    match_matched = api_base_data["match_matched"]
    
    initial_matched = run.matched_count
    
    response = test_client.post(f"/api/v1/reconciliation/matches/{match_matched.id}/confirm", headers=headers)
    assert response.status_code == 200
    
    db_session.refresh(run)
    db_session.refresh(match_matched)
    
    assert match_matched.status == "MATCHED"
    assert run.matched_count == initial_matched # Count unchanged

def test_confirm_match_not_found(test_client: TestClient, auth_headers: tuple):
    headers, _ = auth_headers
    random_id = str(uuid.uuid4())
    
    response = test_client.post(f"/api/v1/reconciliation/matches/{random_id}/confirm", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Match not found"

def test_confirm_match_cross_firm_isolation(test_client: TestClient, db_session: Session, api_base_data: dict):
    firm2 = Firm(name="Other Firm 2")
    db_session.add(firm2)
    db_session.flush()

    user2 = User(name="Other User 2", email="other2@firm.com", password_hash="hash", firm_id=firm2.id)
    db_session.add(user2)
    db_session.commit()

    token2 = create_access_token(data={"sub": str(user2.id)})
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    match_review = api_base_data["match_review"]
    
    response = test_client.post(f"/api/v1/reconciliation/matches/{match_review.id}/confirm", headers=headers2)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this match"

def test_confirm_match_transaction_rollback(test_client: TestClient, db_session: Session, api_base_data: dict, auth_headers: tuple, monkeypatch):
    headers, _ = auth_headers
    run = api_base_data["run"]
    match_review = api_base_data["match_review"]
    
    initial_matched = run.matched_count
    initial_review = run.review_count
    
    # Mock commit to fail
    import sqlalchemy.orm
    def mock_commit(*args, **kwargs):
        raise Exception("DB Error")
    monkeypatch.setattr(sqlalchemy.orm.Session, 'commit', mock_commit)
    
    response = test_client.post(f"/api/v1/reconciliation/matches/{match_review.id}/confirm", headers=headers)
    assert response.status_code == 500
    
    # Use a new session to verify the rollback worked
    new_session = SessionLocal()
    run_db = new_session.query(ReconciliationRun).get(run.id)
    match_db = new_session.query(Match).get(match_review.id)
    
    assert match_db.status == "NEEDS_REVIEW"
    assert run_db.matched_count == initial_matched
    assert run_db.review_count == initial_review
    new_session.close()
