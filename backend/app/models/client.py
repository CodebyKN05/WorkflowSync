import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Uuid, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    firm_id = Column(Uuid, ForeignKey("firms.id"), nullable=False)
    name = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=True)
    currency = Column(String(3), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    firm = relationship("Firm", back_populates="clients")
