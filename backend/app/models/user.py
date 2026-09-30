"""
app/models/user.py
-------------------
ORM model for the `users` table — the master identity record for every
Candidate, Recruiter, and Admin. Belongs in: backend/app/models/user.py
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'candidate' | 'recruiter' | 'admin'
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)  # PHASE 2: OTP email verification
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # One-to-one profile relationships (only one will be populated per user)
    candidate_profile = relationship("Candidate", back_populates="user", uselist=False, cascade="all, delete")
    # PHASE 3: Recruiter now has a second FK (approved_by) to users, so the
    # join condition for THIS relationship must be pinned to user_id explicitly
    # or SQLAlchemy can't tell which FK column to use.
    recruiter_profile = relationship(
        "Recruiter", back_populates="user", uselist=False, cascade="all, delete",
        foreign_keys="Recruiter.user_id",
    )
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
