from sqlalchemy import Column, Integer, String, Float, DateTime, func

from core.database import Base


class StrategySetting(Base):
    __tablename__ = "strategy_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)  # e.g. "min_risk_reward_ratio"
    value = Column(Float, nullable=False)                               # e.g. 2.0
    description = Column(String(255), nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())