import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.firm import Firm
from app.models.client import Client
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
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
        session.close()

client = TestClient(app, raise_server_exceptions=False)

def test_get_my_firm(db_session):
    # Setup firm and user
    firm = Firm(name="My Special Firm")
    db_session.add(firm)
    db_session.flush()
    
    user = User(
        name="Firm User",
        email="firmuser@example.com",
        password_hash=get_password_hash("password"),
        firm_id=firm.id
    )
    db_session.add(user)
    db_session.commit()
    
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Authenticated request
    response = client.get("/api/v1/firms/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(firm.id)
    assert data["name"] == "My Special Firm"
    assert "created_at" in data
    
    # Unauthenticated request
    response = client.get("/api/v1/firms/me")
    assert response.status_code == 401

def test_get_firm_clients(db_session):
    # Setup firms
    firm1 = Firm(name="Firm 1")
    firm2 = Firm(name="Firm 2")
    db_session.add_all([firm1, firm2])
    db_session.flush()
    
    # Setup users
    user1 = User(
        name="User 1",
        email="user1@example.com",
        password_hash=get_password_hash("password"),
        firm_id=firm1.id
    )
    db_session.add(user1)
    db_session.flush()
    
    # Setup clients
    client1_f1 = Client(name="Client A", currency="USD", firm_id=firm1.id)
    client2_f1 = Client(name="Client B", currency="EUR", firm_id=firm1.id)
    client1_f2 = Client(name="Client C", currency="GBP", firm_id=firm2.id)
    
    db_session.add_all([client1_f1, client2_f1, client1_f2])
    db_session.commit()
    
    token = create_access_token({"sub": str(user1.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Authenticated request
    response = client.get("/api/v1/clients", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Should only return clients for firm1
    assert len(data) == 2
    client_names = [c["name"] for c in data]
    assert "Client A" in client_names
    assert "Client B" in client_names
    assert "Client C" not in client_names
    
    for c in data:
        assert c["firm_id"] == str(firm1.id)
        
    # Unauthenticated request
    response = client.get("/api/v1/clients")
    assert response.status_code == 401

def test_get_firm_clients_empty(db_session):
    firm = Firm(name="Empty Firm")
    db_session.add(firm)
    db_session.flush()
    
    user = User(
        name="Empty User",
        email="empty@example.com",
        password_hash=get_password_hash("password"),
        firm_id=firm.id
    )
    db_session.add(user)
    db_session.commit()
    
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/clients", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
