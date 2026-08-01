from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship

from core.database import Base


class SignalEvent(Base):
    __tablename__ = "signal_events"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False, index=True)

    event_type = Column(String(30), nullable=False)  # e.g. "created", "hit_tp", "hit_sl", "invalidated", "expired"
    price_at_event = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    signal = relationship("Signal")