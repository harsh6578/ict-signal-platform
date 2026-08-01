from sqlalchemy import Column, Integer, String, Text, Boolean

from core.database import Base


class ICTConcept(Base):
    __tablename__ = "ict_concepts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)   # e.g. "BOS", "CHOCH", "FVG"
    name = Column(String(100), nullable=False)                           # e.g. "Break of Structure"
    category = Column(String(50), nullable=True)                        # e.g. "market_structure", "liquidity", "pd_array"
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)