import uuid
import fitz
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.client import Client
from app.core.exceptions import AppException
from app.core.config import settings

router = APIRouter()

@router.post("/upload")
def upload_invoice(
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
        
    if not content.startswith(b"%PDF-"):
        raise AppException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format. Only PDF files are allowed."
        )
        
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupt or invalid PDF file."
        )
        
    extracted_text = ""
    try:
        for page in doc:
            text = page.get_text("text")
            if isinstance(text, str):
                extracted_text += text + "\n"
    except Exception:
        doc.close()
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to extract text from PDF."
        )
    finally:
        doc.close()

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "Invoice upload and extraction successful",
        "extracted_text": extracted_text.strip()
    }
