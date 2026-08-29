import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Uuid, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped
from app.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.match import Match

class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id = Column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    client_id = Column(Uuid, ForeignKey("clients.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    matched_count = Column(Integer, nullable=False, default=0)
    review_count = Column(Integer, nullable=False, default=0)
    unmatched_count = Column(Integer, nullable=False, default=0)
    duplicate_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False)

    client: Mapped["Client"] = relationship("Client", back_populates="reconciliation_runs")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="reconciliation_run")
