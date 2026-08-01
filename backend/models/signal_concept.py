from sqlalchemy import Column, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from core.database import Base


class SignalConcept(Base):
    __tablename__ = "signal_concepts"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey("ict_concepts.id"), nullable=False, index=True)
    timeframe_id = Column(Integer, ForeignKey("timeframes.id"), nullable=True)  # supports multi-timeframe confluence

    confidence_weight = Column(Float, nullable=True)  # how much this concept contributed to the overall score
    details = Column(Text, nullable=True)             # free-text/JSON notes specific to this occurrence

    signal = relationship("Signal", back_populates="concepts")
    concept = relationship("ICTConcept")
    timeframe = relationship("Timeframe")