import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Uuid
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Firm(Base):
    __tablename__ = "firms"

    id = Column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
