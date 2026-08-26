import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Uuid, ForeignKey
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    firm_id = Column(Uuid, ForeignKey("firms.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
