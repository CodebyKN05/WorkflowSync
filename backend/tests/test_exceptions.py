import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.core.exceptions import AppException, app_exception_handler, global_exception_handler

# Create a local test app to isolate exception handler testing
app = FastAPI()
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

@app.get("/app-error")
def trigger_app_error():
    raise AppException(status_code=400, detail="Custom application error")

@app.get("/unexpected-error")
def trigger_unexpected_error():
    raise ValueError("This is a secret internal error detail")

@app.get("/http-error")
def trigger_http_error():
    raise HTTPException(status_code=404, detail="Not found error")

client = TestClient(app, raise_server_exceptions=False)

def test_app_exception_handler():
    """Verify custom application exception returns the expected status code and JSON body."""
    response = client.get("/app-error")
    assert response.status_code == 400
    assert response.json() == {"detail": "Custom application error"}

def test_global_exception_handler():
    """Verify unexpected exception returns HTTP 500 with only the safe generic message."""
    response = client.get("/unexpected-error")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "secret" not in response.text

def test_http_exception_behavior_preserved():
    """Verify FastAPI's normal HTTPException behavior is not broken."""
    response = client.get("/http-error")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found error"}

def test_existing_health_endpoint():
    """Verify the existing /health endpoint still returns 200."""
    from app.main import app as main_app
    main_client = TestClient(main_app)
    response = main_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "WorkflowSync backend is running"}
