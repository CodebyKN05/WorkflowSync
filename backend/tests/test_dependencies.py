import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.dependencies import get_db

def test_get_db_provides_usable_session():
    """Verify get_db yields a real SQLAlchemy Session that can connect."""
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        assert isinstance(db_session, Session)
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

def test_get_db_closes_session():
    """Verify that get_db properly closes the session upon completion."""
    with patch("app.api.dependencies.SessionLocal") as mock_session_local:
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        db_gen = get_db()
        db_session = next(db_gen)
        
        assert db_session == mock_session
        
        try:
            next(db_gen)
        except StopIteration:
            pass
            
        mock_session.close.assert_called_once()

def test_get_db_in_fastapi():
    """Verify get_db works natively as a FastAPI dependency."""
    app = FastAPI()
    
    # Minimal test-only endpoint strictly internal to this test
    @app.get("/test-db-dependency")
    def test_endpoint(db: Session = Depends(get_db)):
        return {"value": db.execute(text("SELECT 1")).scalar()}
        
    client = TestClient(app)
    response = client.get("/test-db-dependency")
    
    assert response.status_code == 200
    assert response.json() == {"value": 1}
