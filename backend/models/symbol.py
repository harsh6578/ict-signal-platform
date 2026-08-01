from sqlalchemy import Column, Integer, String, Boolean, DateTime, func

from core.database import Base


class Symbol(Base):
    __tablename__ = "symbols"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)  # e.g. "BTCUSDT"
    base_asset = Column(String(10), nullable=False)   # e.g. "BTC"
    quote_asset = Column(String(10), nullable=False)  # e.g. "USDT"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())