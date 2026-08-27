import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Uuid, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from app.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.firm import Firm
    from app.models.invoice import Invoice

class Client(Base):
    __tablename__ = "clients"

    id = Column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    firm_id = Column(Uuid, ForeignKey("firms.id"), nullable=False)
    name = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=True)
    currency = Column(String(3), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    firm: Mapped["Firm"] = relationship("Firm", back_populates="clients")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="client")
