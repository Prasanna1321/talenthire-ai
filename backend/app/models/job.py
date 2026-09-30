"""
app/models/job.py
------------------
ORM models for `jobs` and `applications`.
Belongs in: backend/app/models/job.py
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.recruiter_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(ARRAY(String), nullable=False)
    experience_level = Column(String(30))  # entry | mid | senior
    location = Column(String(100))
    job_type = Column(String(30), default="full-time")
    status = Column(String(20), default="open")  # open | closed | draft
    created_at = Column(DateTime, server_default=func.now())

    recruiter = relationship("Recruiter", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete")
    questions = relationship("InterviewQuestion", back_populates="job", cascade="all, delete")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),)

    application_id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.resume_id", ondelete="SET NULL"))
    match_score = Column(Numeric(5, 2))
    status = Column(String(30), default="applied")
    applied_at = Column(DateTime, server_default=func.now())

    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume")
    interview_sessions = relationship("InterviewSession", back_populates="application", cascade="all, delete")
