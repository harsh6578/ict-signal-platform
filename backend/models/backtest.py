from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from core.database import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    timeframe_id = Column(Integer, ForeignKey("timeframes.id"), nullable=False, index=True)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    total_signals = Column(Integer, default=0, nullable=False)
    win_count = Column(Integer, default=0, nullable=False)
    loss_count = Column(Integer, default=0, nullable=False)
    win_rate = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    symbol = relationship("Symbol")
    timeframe = relationship("Timeframe")
    trades = relationship("BacktestTrade", back_populates="run", cascade="all, delete-orphan")


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("backtest_runs.id"), nullable=False, index=True)

    direction = Column(String(4), nullable=False)  # "BUY" or "SELL"
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    outcome = Column(String(20), nullable=False)  # "win", "loss", "breakeven"

    entry_time = Column(DateTime(timezone=True), nullable=False)
    exit_time = Column(DateTime(timezone=True), nullable=True)

    run = relationship("BacktestRun", back_populates="trades")