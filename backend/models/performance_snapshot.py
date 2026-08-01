from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from core.database import Base


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=True, index=True)  # null = across all symbols

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    total_signals = Column(Integer, default=0, nullable=False)
    win_count = Column(Integer, default=0, nullable=False)
    loss_count = Column(Integer, default=0, nullable=False)
    win_rate = Column(Float, nullable=True)
    avg_risk_reward = Column(Float, nullable=True)

    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    symbol = relationship("Symbol")