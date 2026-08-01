from sqlalchemy import Column, Integer, String, Time, Boolean

from core.database import Base


class MarketSession(Base):
    __tablename__ = "market_sessions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False)   # e.g. "london", "new_york", "asia", "silver_bullet_am"
    name = Column(String(100), nullable=False)               # e.g. "London Killzone"
    start_time_utc = Column(Time, nullable=False)
    end_time_utc = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)