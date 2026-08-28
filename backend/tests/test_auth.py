import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_password_hash, verify_password, create_access_token
import jwt
from app.core.config import settings
from datetime import timedelta
import uuid
from app.models.firm import Firm
from app.models.user import User
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

def test_password_hashing():
    password = "supersecretpassword"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_registration(db_session):
    # Setup firm
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.commit()
    db_session.refresh(firm)
    
    register_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "mypassword123",
        "firm_id": str(firm.id)
    }
    
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["firm_id"] == str(firm.id)
    assert "password" not in data
    assert "password_hash" not in data
    
    # Check DB
    user_in_db = db_session.query(User).filter(User.email == "test@example.com").first()
    assert user_in_db is not None
    assert user_in_db.password_hash != "mypassword123"
    
    # Duplicate email
    response2 = client.post("/api/v1/auth/register", json=register_data)
    assert response2.status_code == 409

def test_login(db_session):
    # Setup firm and user
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()
    
    user = User(
        name="Login User",
        email="login@example.com",
        password_hash=get_password_hash("mypassword"),
        firm_id=firm.id
    )
    db_session.add(user)
    db_session.commit()
    
    # Valid login
    login_data = {"email": "login@example.com", "password": "mypassword"}
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
    
    # Invalid password
    response = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "wrong"})
    assert response.status_code == 401
    
    # Unknown email
    response = client.post("/api/v1/auth/login", json={"email": "unknown@example.com", "password": "mypassword"})
    assert response.status_code == 401

def test_current_user_endpoint(db_session):
    firm = Firm(name="Test Firm")
    db_session.add(firm)
    db_session.flush()
    
    user = User(
        name="Me User",
        email="me@example.com",
        password_hash=get_password_hash("mypassword"),
        firm_id=firm.id
    )
    db_session.add(user)
    db_session.commit()
    
    # Get token
    token = create_access_token({"sub": str(user.id)})
    
    # Valid token
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert "password_hash" not in data
    
    # No token
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    
    # Invalid token
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401

def test_token_behavior():
    # Token can be decoded
    token = create_access_token({"sub": "test-id"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "test-id"
    assert "exp" in payload
    
    # Expired token
    expired_token = create_access_token({"sub": "test-id"}, expires_delta=timedelta(minutes=-10))
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(expired_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
