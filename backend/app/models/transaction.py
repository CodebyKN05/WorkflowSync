import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Date, Numeric, Uuid, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from app.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.firm import Firm
    from app.models.client import Client
    from app.models.match import Match

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    client_id = Column(Uuid, ForeignKey("clients.id"), nullable=False)
    transaction_date = Column(Date, nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    reference = Column(String(255), nullable=True)
    source_file = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    client: Mapped["Client"] = relationship("Client", back_populates="transactions")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="transaction")
