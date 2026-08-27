import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Date, Numeric, Uuid, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from app.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.client import Client

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    client_id = Column(Uuid, ForeignKey("clients.id"), nullable=False)
    invoice_number = Column(String(100), nullable=False)
    vendor = Column(String(255), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    pdf_path = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    client: Mapped["Client"] = relationship("Client", back_populates="invoices")
