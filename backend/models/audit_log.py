from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # null = system-generated event

    action = Column(String(100), nullable=False)  # e.g. "signal_generated", "settings_changed", "login"
    details = Column(Text, nullable=True)

    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")