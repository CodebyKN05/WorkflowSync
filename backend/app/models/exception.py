import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Uuid, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped
from app.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.transaction import Transaction

class ReconciliationException(Base):
    __tablename__ = "exceptions"

    id = Column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    invoice_id = Column(Uuid, ForeignKey("invoices.id"), nullable=True)
    transaction_id = Column(Uuid, ForeignKey("transactions.id"), nullable=True)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="exceptions")
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="exceptions")
