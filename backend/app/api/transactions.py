import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.client import Client
from app.core.exceptions import AppException
from app.core.config import settings
from app.services.transaction_parser import parse_transaction_csv
from app.services.transaction_validator import validate_parsed_transactions

router = APIRouter()

@router.post("/upload")
def upload_transaction_csv(
    client_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify client ownership through firm association
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    if client.firm_id != current_user.firm_id:  # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this client"
        )

    content = file.file.read()

    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise AppException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    if file.filename and not file.filename.lower().endswith(".csv"):
        raise AppException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format. Only CSV files are allowed."
        )

    csv_text = content.decode("utf-8-sig", errors="replace")
    parsed_rows = parse_transaction_csv(csv_text)
    validate_parsed_transactions(parsed_rows)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "Bank CSV upload accepted."
    }
