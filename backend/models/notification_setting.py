from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from core.database import Base


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    email_enabled = Column(Boolean, default=True, nullable=False)
    min_confidence_score = Column(Integer, default=70, nullable=False)  # only email signals above this score

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")