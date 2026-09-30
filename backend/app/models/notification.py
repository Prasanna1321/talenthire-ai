"""
app/models/notification.py
---------------------------
ORM model for `notifications` — in-app alerts for all three roles
(application status changes, interview scheduling, feedback ready, etc).
Belongs in: backend/app/models/notification.py
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    notification_type = Column(String(30), default="info")  # info | success | warning | interview | application
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="notifications")
