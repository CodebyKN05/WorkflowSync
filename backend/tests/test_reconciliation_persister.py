import uuid
import pytest
from datetime import date
from decimal import Decimal

from app.models.firm import Firm
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.transaction import Transaction
from app.models.reconciliation_run import ReconciliationRun
from app.models.match import Match

from app.services.confidence_scorer import ConfidenceScoreResult
from app.services.result_classifier import ClassificationResult, ResultCategory
from app.services.explainability_service import ExplanationResult
from app.services.reconciliation_persister import MatchData, persist_reconciliation_run

from sqlalchemy.exc import OperationalError
from app.core.database import engine, Base, SessionLocal

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

@pytest.fixture
def base_data(db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()

    client = Client(name="Test Client", industry="Tech", currency="USD", firm_id=firm.id)
    db_session.add(client)
    db_session.flush()

    invoice1 = Invoice(client_id=client.id, invoice_number="INV-1", vendor="Acme", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("100.00"), currency="USD")
    invoice2 = Invoice(client_id=client.id, invoice_number="INV-2", vendor="Beta", invoice_date=date(2023, 1, 1), due_date=date(2023, 1, 31), amount=Decimal("200.00"), currency="USD")
    transaction1 = Transaction(client_id=client.id, transaction_date=date(2023, 1, 5), description="Acme Inc", amount=Decimal("-100.00"), currency="USD")
    transaction2 = Transaction(client_id=client.id, transaction_date=date(2023, 1, 6), description="Beta Corp", amount=Decimal("-200.00"), currency="USD")
    
    db_session.add_all([invoice1, invoice2, transaction1, transaction2])
    db_session.commit()
    
    return {
        "client": client,
        "invoice1": invoice1,
        "invoice2": invoice2,
        "transaction1": transaction1,
        "transaction2": transaction2
    }


def test_persist_successful_run(db_session, base_data):
    client = base_data["client"]
    invoice1 = base_data["invoice1"]
    transaction1 = base_data["transaction1"]

    match_data = [
        MatchData(
            invoice_id=invoice1.id,
            transaction_id=transaction1.id,
            confidence_result=ConfidenceScoreResult(total_score=95.0),
            classification_result=ClassificationResult(category=ResultCategory.MATCHED),
            explanation_result=ExplanationResult(reasons=["Amount: Exact match", "Vendor: 100% similar"])
        )
    ]

    run = persist_reconciliation_run(db_session, client.id, match_data)

    assert run.id is not None
    assert run.client_id == client.id
    assert run.matched_count == 1  # type: ignore
    assert run.review_count == 0  # type: ignore
    assert run.status == "completed"  # type: ignore

    matches = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).all()
    assert len(matches) == 1
    assert matches[0].invoice_id == invoice1.id
    assert matches[0].transaction_id == transaction1.id
    assert matches[0].score == Decimal("95.00")
    assert matches[0].status == "MATCHED"  # type: ignore
    assert matches[0].reason == "Amount: Exact match\nVendor: 100% similar"  # type: ignore


def test_persist_multiple_classifications_and_counts(db_session, base_data):
    client = base_data["client"]
    invoice1 = base_data["invoice1"]
    invoice2 = base_data["invoice2"]
    transaction1 = base_data["transaction1"]
    transaction2 = base_data["transaction2"]

    match_data = [
        MatchData(
            invoice_id=invoice1.id,
            transaction_id=transaction1.id,
            confidence_result=ConfidenceScoreResult(total_score=95.0),
            classification_result=ClassificationResult(category=ResultCategory.MATCHED),
            explanation_result=ExplanationResult(reasons=[])
        ),
        MatchData(
            invoice_id=invoice2.id,
            transaction_id=transaction2.id,
            confidence_result=ConfidenceScoreResult(total_score=75.0),
            classification_result=ClassificationResult(category=ResultCategory.NEEDS_REVIEW),
            explanation_result=ExplanationResult(reasons=[])
        )
    ]

    run = persist_reconciliation_run(db_session, client.id, match_data)

    assert run.matched_count == 1  # type: ignore
    assert run.review_count == 1  # type: ignore
    assert run.unmatched_count == 0  # type: ignore
    assert run.duplicate_count == 0  # type: ignore
    
    matches = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).all()
    assert len(matches) == 2


def test_persist_filters_intra_run_duplicates(db_session, base_data):
    client = base_data["client"]
    invoice1 = base_data["invoice1"]
    transaction1 = base_data["transaction1"]

    match_data = [
        MatchData(
            invoice_id=invoice1.id,
            transaction_id=transaction1.id,
            confidence_result=ConfidenceScoreResult(total_score=95.0),
            classification_result=ClassificationResult(category=ResultCategory.MATCHED),
            explanation_result=ExplanationResult(reasons=[])
        ),
        MatchData(
            invoice_id=invoice1.id,
            transaction_id=transaction1.id,
            confidence_result=ConfidenceScoreResult(total_score=90.0),
            classification_result=ClassificationResult(category=ResultCategory.DUPLICATE),
            explanation_result=ExplanationResult(reasons=[])
        )
    ]

    run = persist_reconciliation_run(db_session, client.id, match_data)

    assert run.matched_count == 1  # type: ignore
    assert run.duplicate_count == 0  # type: ignore
    
    matches = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).all()
    assert len(matches) == 1
    assert matches[0].score == Decimal("95.00")


def test_persist_rerun_preserves_history(db_session, base_data):
    client = base_data["client"]
    invoice1 = base_data["invoice1"]
    transaction1 = base_data["transaction1"]

    match_data_run1 = [
        MatchData(
            invoice_id=invoice1.id,
            transaction_id=transaction1.id,
            confidence_result=ConfidenceScoreResult(total_score=80.0),
            classification_result=ClassificationResult(category=ResultCategory.NEEDS_REVIEW),
            explanation_result=ExplanationResult(reasons=[])
        )
    ]

    run1 = persist_reconciliation_run(db_session, client.id, match_data_run1)

    match_data_run2 = [
        MatchData(
            invoice_id=invoice1.id,
            transaction_id=transaction1.id,
            confidence_result=ConfidenceScoreResult(total_score=90.0),
            classification_result=ClassificationResult(category=ResultCategory.MATCHED),
            explanation_result=ExplanationResult(reasons=[])
        )
    ]

    run2 = persist_reconciliation_run(db_session, client.id, match_data_run2)

    assert run1.id != run2.id

    matches_run1 = db_session.query(Match).filter(Match.reconciliation_run_id == run1.id).all()
    assert len(matches_run1) == 1
    assert matches_run1[0].status == "NEEDS_REVIEW"  # type: ignore

    matches_run2 = db_session.query(Match).filter(Match.reconciliation_run_id == run2.id).all()
    assert len(matches_run2) == 1
    assert matches_run2[0].status == "MATCHED"  # type: ignore

    total_matches = db_session.query(Match).join(ReconciliationRun).filter(ReconciliationRun.client_id == client.id).count()
    assert total_matches == 2


def test_persist_unmatched_invoice_count(db_session, base_data):
    client = base_data["client"]
    invoice1 = base_data["invoice1"]
    transaction1 = base_data["transaction1"]

    match_data = [
        MatchData(
            invoice_id=invoice1.id,
            transaction_id=transaction1.id,
            confidence_result=ConfidenceScoreResult(total_score=30.0),
            classification_result=ClassificationResult(category=ResultCategory.UNMATCHED),
            explanation_result=ExplanationResult(reasons=[])
        )
    ]

    # Passing unmatched_invoice_count=2 to simulate 2 invoices with no candidates
    run = persist_reconciliation_run(db_session, client.id, match_data, unmatched_invoice_count=2)

    assert run.matched_count == 0  # type: ignore
    assert run.unmatched_count == 3  # type: ignore (1 from MatchData + 2 explicit)
    assert run.review_count == 0  # type: ignore
    assert run.duplicate_count == 0  # type: ignore

    matches = db_session.query(Match).filter(Match.reconciliation_run_id == run.id).all()
    assert len(matches) == 1
    assert matches[0].status == "UNMATCHED"  # type: ignore


def test_persist_rollback_on_failure(db_session, base_data):
    client = base_data["client"]
    invoice1 = base_data["invoice1"]
    
    # Missing transaction ID will trigger DB integrity error
    match_data = [
        MatchData(
            invoice_id=invoice1.id,
            transaction_id=uuid.uuid4(), # Does not exist in DB
            confidence_result=ConfidenceScoreResult(total_score=95.0),
            classification_result=ClassificationResult(category=ResultCategory.MATCHED),
            explanation_result=ExplanationResult(reasons=[])
        )
    ]

    with pytest.raises(Exception):
        persist_reconciliation_run(db_session, client.id, match_data)

    runs = db_session.query(ReconciliationRun).filter(ReconciliationRun.client_id == client.id).count()
    assert runs == 0

    matches = db_session.query(Match).join(ReconciliationRun).filter(ReconciliationRun.client_id == client.id).count()
    assert matches == 0

def test_persist_reconciliation_with_exceptions(db_session):
    firm = Firm(name="Persist Firm")
    client = Client(name="Persist Client", currency="USD")
    firm.clients.append(client)
    db_session.add(firm)
    db_session.flush()

    from app.models.exception import ReconciliationException
    exceptions = [
        ReconciliationException(
            type="DUMMY_ERROR",
            description="Dummy 1",
            status="OPEN"
        ),
        ReconciliationException(
            type="DUMMY_ERROR_2",
            description="Dummy 2",
            status="OPEN"
        )
    ]

    run = persist_reconciliation_run(
        db=db_session,
        client_id=client.id,
        match_results=[],
        unmatched_invoice_count=0,
        exceptions=exceptions
    )

    # B. Exception persistence
    assert run.id is not None
    db_session.refresh(run)
    assert len(run.exceptions) == 2
    assert run.exceptions[0].reconciliation_run_id == run.id
    assert run.exceptions[1].reconciliation_run_id == run.id

def test_persist_repeated_run_isolation(db_session):
    firm = Firm(name="Repeated Firm")
    client = Client(name="Repeated Client", currency="USD")
    firm.clients.append(client)
    db_session.add(firm)
    db_session.flush()

    from app.models.exception import ReconciliationException
    exc1 = ReconciliationException(type="RUN_A_EXC", description="A", status="OPEN")
    exc2 = ReconciliationException(type="RUN_B_EXC", description="B", status="OPEN")

    run_a = persist_reconciliation_run(
        db=db_session,
        client_id=client.id,
        match_results=[],
        exceptions=[exc1]
    )

    run_b = persist_reconciliation_run(
        db=db_session,
        client_id=client.id,
        match_results=[],
        exceptions=[exc2]
    )

    db_session.refresh(run_a)
    db_session.refresh(run_b)

    # C. Repeated-run isolation
    assert len(run_a.exceptions) == 1
    assert run_a.exceptions[0].type == "RUN_A_EXC"
    
    assert len(run_b.exceptions) == 1
    assert run_b.exceptions[0].type == "RUN_B_EXC"

def test_persist_rollback_on_exception_failure(db_session):
    firm = Firm(name="Rollback Firm")
    client = Client(name="Rollback Client", currency="USD")
    firm.clients.append(client)
    db_session.add(firm)
    db_session.flush()

    from app.models.exception import ReconciliationException
    # Setting an invalid/non-existent foreign key to force integrity error
    bad_exc = ReconciliationException(
        type="BAD_EXC",
        description="Bad",
        status="OPEN",
        invoice_id=uuid.uuid4() # Fails integrity
    )

    with pytest.raises(Exception):
        persist_reconciliation_run(
            db=db_session,
            client_id=client.id,
            match_results=[],
            exceptions=[bad_exc]
        )

    # D. Rollback verification
    runs = db_session.query(ReconciliationRun).filter(ReconciliationRun.client_id == client.id).count()
    assert runs == 0

    exceptions_in_db = db_session.query(ReconciliationException).filter(ReconciliationException.description == "Bad").count()
    # It should not persist the bad exception
    assert exceptions_in_db == 0

def test_persist_regression_zero_exceptions(db_session):
    firm = Firm(name="Regression Firm")
    client = Client(name="Regression Client", currency="USD")
    firm.clients.append(client)
    db_session.add(firm)
    db_session.flush()

    invoice = Invoice(client_id=client.id, invoice_number="INV1", vendor="V1", invoice_date=date(2023,1,1), due_date=date(2023,1,31), amount=Decimal("100"), currency="USD")
    transaction = Transaction(client_id=client.id, transaction_date=date(2023,1,1), description="V1", amount=Decimal("-100"), currency="USD")
    db_session.add_all([invoice, transaction])
    db_session.flush()

    match_data = [
        MatchData(
            invoice_id=invoice.id,
            transaction_id=transaction.id,
            confidence_result=ConfidenceScoreResult(total_score=Decimal("100.0")),
            classification_result=ClassificationResult(category=ResultCategory.MATCHED),
            explanation_result=ExplanationResult(reasons=["Test"])
        )
    ]

    # E. Regression (calling without exceptions parameter)
    run = persist_reconciliation_run(
        db=db_session,
        client_id=client.id,
        match_results=match_data
    )

    db_session.refresh(run)
    assert run.matched_count == 1
    assert len(run.matches) == 1
    assert len(run.exceptions) == 0
