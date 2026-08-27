import pytest
import uuid
from datetime import datetime, timezone
from typing import cast
from sqlalchemy.exc import OperationalError, IntegrityError
from app.core.database import engine, Base, SessionLocal
from app.models.firm import Firm
from app.models.client import Client
from app.models.reconciliation_run import ReconciliationRun

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

def test_reconciliation_run_metadata():
    assert ReconciliationRun.__tablename__ == "reconciliation_runs"
    
    columns = {c.name: c for c in ReconciliationRun.__table__.columns}
    assert "id" in columns
    assert "client_id" in columns
    assert "started_at" in columns
    assert "completed_at" in columns
    assert "matched_count" in columns
    assert "review_count" in columns
    assert "unmatched_count" in columns
    assert "duplicate_count" in columns
    assert "status" in columns
    
    # 9 explicit columns
    assert len(columns) == 9
    
    # verify expected nullabilities where explicit
    assert columns["completed_at"].nullable is True
    assert columns["matched_count"].nullable is False
    assert columns["review_count"].nullable is False
    assert columns["unmatched_count"].nullable is False
    assert columns["duplicate_count"].nullable is False

def test_reconciliation_run_construction_and_persistence(db_session):
    firm = Firm(name="Recon Firm")
    client = Client(name="Recon Client", currency="USD")
    firm.clients.append(client)
    
    db_session.add(firm)
    db_session.commit()
    
    run = ReconciliationRun(
        client_id=client.id,
        matched_count=10,
        review_count=2,
        unmatched_count=5,
        duplicate_count=1,
        status="COMPLETED"
    )
    
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    
    assert isinstance(run.id, uuid.UUID)
    assert run.client_id == client.id
    assert run.started_at is not None
    assert run.completed_at is None
    assert run.matched_count == 10
    assert run.review_count == 2
    assert run.unmatched_count == 5
    assert run.duplicate_count == 1
    assert run.status == "COMPLETED"

def test_reconciliation_run_requires_client(db_session):
    run = ReconciliationRun(
        matched_count=10,
        review_count=2,
        unmatched_count=5,
        duplicate_count=1,
        status="COMPLETED"
    )
    
    db_session.add(run)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
        
    db_session.rollback()

def test_reconciliation_run_requires_status(db_session):
    firm = Firm(name="Recon Status Firm")
    client = Client(name="Recon Status Client", currency="USD")
    firm.clients.append(client)
    
    db_session.add(firm)
    db_session.commit()
    
    run = ReconciliationRun(
        client_id=client.id,
        matched_count=10,
        review_count=2,
        unmatched_count=5,
        duplicate_count=1
    )
    
    db_session.add(run)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
        
    db_session.rollback()

def test_reconciliation_run_count_defaults(db_session):
    firm = Firm(name="Recon Default Firm")
    client = Client(name="Recon Default Client", currency="USD")
    firm.clients.append(client)
    
    db_session.add(firm)
    db_session.commit()
    
    run = ReconciliationRun(
        client_id=client.id,
        status="IN_PROGRESS"
    )
    
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    
    assert run.matched_count == 0
    assert run.review_count == 0
    assert run.unmatched_count == 0
    assert run.duplicate_count == 0

def test_reconciliation_run_client_relationship(db_session):
    firm = Firm(name="Recon Rel Firm")
    client = Client(name="Recon Rel Client", currency="USD")
    firm.clients.append(client)
    
    run = ReconciliationRun(
        status="IN_PROGRESS"
    )
    client.reconciliation_runs.append(run)
    
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(client)
    db_session.refresh(run)
    
    assert run.client_id == client.id
    assert run.client.id == client.id
    assert len(cast(list[ReconciliationRun], client.reconciliation_runs)) == 1
    assert client.reconciliation_runs[0].id == run.id

def test_reconciliation_run_completed_at_update(db_session):
    firm = Firm(name="Recon Update Firm")
    client = Client(name="Recon Update Client", currency="USD")
    firm.clients.append(client)
    
    db_session.add(firm)
    db_session.commit()
    
    run = ReconciliationRun(
        client_id=client.id,
        status="IN_PROGRESS"
    )
    
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    
    assert run.completed_at is None
    
    completion_time = datetime.now(timezone.utc)
    run.completed_at = completion_time
    run.status = "COMPLETED"
    
    db_session.commit()
    db_session.refresh(run)
    
    assert run.completed_at is not None
    assert run.status == "COMPLETED"
