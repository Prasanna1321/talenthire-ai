"""
app/models/otp.py
--------------------
Phase 2: Email OTP verification + password reset tokens.
Belongs in: backend/app/models/otp.py
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from app.database import Base


class EmailOTP(Base):
    __tablename__ = "email_otps"

    otp_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    otp_hash = Column(String(255), nullable=False)
    purpose = Column(String(30), nullable=False)  # email_verification | password_reset
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
