"""
app/models/resume.py
---------------------
ORM model for `resumes` — uploaded files plus the output of the resume
parsing and classification pipeline (ml/resume_parser, ml/resume_classifier).
Belongs in: backend/app/models/resume.py
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    resume_id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    raw_text = Column(Text)
    extracted_skills = Column(ARRAY(String))
    predicted_category = Column(String(100))
    prediction_confidence = Column(Numeric(5, 4))
    embedding = Column(ARRAY(Numeric))  # sentence-transformer vector, used for similarity search
    # PHASE 4: versioning, identity extraction (for consistency checks), ATS scoring
    version_number = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    extracted_name = Column(String(150), nullable=True)
    extracted_email = Column(String(150), nullable=True)
    extracted_phone = Column(String(20), nullable=True)
    ats_score = Column(Numeric(5, 2), nullable=True)
    ats_breakdown = Column(JSONB, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())

    candidate = relationship("Candidate", back_populates="resumes")
