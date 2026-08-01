from sqlalchemy import Column, Integer, String

from core.database import Base


class Timeframe(Base):
    __tablename__ = "timeframes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)  # e.g. "1m", "5m", "15m", "1h", "4h", "1d", "1M"
    label = Column(String(30), nullable=False)              # e.g. "1 Minute", "1 Hour", "1 Month"
    minutes = Column(Integer, nullable=False)               # numeric duration, e.g. 1, 5, 60, 240, 1440, 43200