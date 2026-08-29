import uuid
import fitz
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.client import Client
from app.models.invoice import Invoice
from app.core.exceptions import AppException
from app.core.config import settings
from app.services.invoice_parser import parse_invoice_text
from app.schemas.invoice import InvoiceUploadResponse

router = APIRouter()

@router.post("/upload", response_model=InvoiceUploadResponse)
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

    extracted_text = extracted_text.strip()
    extracted_data = parse_invoice_text(extracted_text)

    missing_fields = []
    if not extracted_data.invoice_number:
        missing_fields.append("invoice_number")
    if not extracted_data.vendor:
        missing_fields.append("vendor")
    if not extracted_data.invoice_date:
        missing_fields.append("invoice_date")
    if not extracted_data.due_date:
        missing_fields.append("due_date")
    if extracted_data.total is None:
        missing_fields.append("amount")
    if not extracted_data.currency:
        missing_fields.append("currency")

    if missing_fields:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invoice could not be persisted because required fields are missing: {', '.join(missing_fields)}"
        )

    db_invoice = Invoice(
        client_id=client.id,
        invoice_number=extracted_data.invoice_number,
        vendor=extracted_data.vendor,
        invoice_date=extracted_data.invoice_date,
        due_date=extracted_data.due_date,
        amount=extracted_data.total,
        currency=extracted_data.currency,
        pdf_path=None
    )

    try:
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
    except Exception:
        db.rollback()
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist invoice to database."
        )

    return {
        "id": db_invoice.id,
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "Invoice uploaded and persisted successfully.",
        "extracted_text": extracted_text,
        "extracted_data": extracted_data,
        "status": db_invoice.status
    }
