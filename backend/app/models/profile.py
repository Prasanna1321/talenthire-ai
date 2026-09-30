"""
app/models/profile.py
----------------------
ORM models for `recruiters` and `candidates` — role-specific profile data
that extends the base `users` table (1-to-1).
Belongs in: backend/app/models/profile.py
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Recruiter(Base):
    __tablename__ = "recruiters"

    recruiter_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name = Column(String(150), nullable=False)
    designation = Column(String(100))
    company_website = Column(String(255))
    # PHASE 3: recruiter approval workflow
    status = Column(String(20), default="pending")  # pending | approved | rejected | suspended
    approved_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="recruiter_profile", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by])  # PHASE 3: which admin approved/rejected this recruiter
    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete")


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    phone = Column(String(20))
    location = Column(String(100))
    highest_education = Column(String(150))
    years_experience = Column(Numeric(4, 1), default=0)
    linkedin_url = Column(String(255))
    github_url = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="candidate_profile")
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete")
    interview_sessions = relationship("InterviewSession", back_populates="candidate", cascade="all, delete")
