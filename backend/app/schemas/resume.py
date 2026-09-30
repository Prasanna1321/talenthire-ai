"""
app/schemas/resume.py
----------------------
Pydantic response models for resume upload, parsing, and classification.
Belongs in: backend/app/schemas/resume.py
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_id: int
    candidate_id: int
    original_filename: Optional[str] = None
    extracted_skills: Optional[List[str]] = None
    version_number: int = 1
    is_current: bool = True
    ats_score: Optional[float] = None
    ats_breakdown: Optional[dict] = None
    uploaded_at: datetime


class ResumeUploadResponse(BaseModel):
    """
    PHASE 4: upload can either succeed immediately (resume populated,
    requires_confirmation=False) or flag a possible identity mismatch with
    the candidate's existing resume (warning populated, resume=None) —
    the frontend then re-submits with force=true to proceed anyway, or
    lets the candidate keep their current resume instead.
    """
    requires_confirmation: bool
    warning: Optional[str] = None
    resume: Optional[ResumeOut] = None


class ResumeParseResult(BaseModel):
    """Internal DTO returned by the ml resume_parser service."""
    raw_text: str
    extracted_skills: List[str]


class ResumeClassificationResult(BaseModel):
    """Internal DTO returned by the ml resume_classifier service."""
    predicted_category: str
    confidence: float


class JobRecommendation(BaseModel):
    job_id: int
    title: str
    company_name: str
    match_score: float
    matched_skills: List[str]
