from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from core.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    timeframe_id = Column(Integer, ForeignKey("timeframes.id"), nullable=False, index=True)

    direction = Column(String(4), nullable=False)  # "BUY" or "SELL"

    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    risk_reward_ratio = Column(Float, nullable=True)

    confidence_score = Column(Float, nullable=False)  # 0-100, computed from signal_concepts
    status = Column(String(20), nullable=False, default="active")  # active, hit_tp, hit_sl, invalidated, expired

    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    symbol = relationship("Symbol")
    timeframe = relationship("Timeframe")
    concepts = relationship("SignalConcept", back_populates="signal", cascade="all, delete-orphan")