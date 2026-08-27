import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Uuid, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship, Mapped
from app.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.transaction import Transaction

class Match(Base):
    __tablename__ = "matches"

    id = Column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    invoice_id = Column(Uuid, ForeignKey("invoices.id"), nullable=False)
    transaction_id = Column(Uuid, ForeignKey("transactions.id"), nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    status = Column(String(32), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="matches")
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="matches")
