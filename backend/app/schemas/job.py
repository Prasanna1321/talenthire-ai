"""
app/schemas/job.py
-------------------
Pydantic request/response models for job postings and applications.
Belongs in: backend/app/schemas/job.py
"""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    title: str = Field(..., max_length=150)
    description: str
    required_skills: List[str]
    experience_level: Literal["entry", "mid", "senior"] = "entry"
    location: Optional[str] = None
    job_type: str = "full-time"


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    experience_level: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    status: Optional[Literal["open", "closed", "draft"]] = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    recruiter_id: int
    title: str
    description: str
    required_skills: List[str]
    experience_level: Optional[str] = None
    location: Optional[str] = None
    job_type: str
    status: str
    created_at: datetime


class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: Optional[int] = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: int
    candidate_id: int
    job_id: int
    resume_id: Optional[int] = None
    match_score: Optional[float] = None
    status: str
    applied_at: datetime


class ApplicationStatusUpdate(BaseModel):
    status: Literal[
        "applied", "shortlisted", "interview_scheduled",
        "interview_completed", "selected", "rejected",
    ]


# ---------------------------------------------------------------------------
# PHASE 8: richer recruiter-facing candidate view (ATS + aptitude + interview
# scores + matched/missing skills all in one place, not just a bare percentage)
# ---------------------------------------------------------------------------
class CandidateDetailOut(BaseModel):
    application_id: int
    candidate_id: int
    full_name: str
    email: str
    status: str
    match_score: Optional[float] = None
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    ats_score: Optional[float] = None
    aptitude_percentage: Optional[float] = None
    interview_score: Optional[float] = None
