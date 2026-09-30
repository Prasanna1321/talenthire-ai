"""
app/schemas/user.py
--------------------
Pydantic response models for user, candidate, and recruiter profile data.
Belongs in: backend/app/schemas/user.py
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class CandidateProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: int
    user_id: int
    phone: Optional[str] = None
    location: Optional[str] = None
    highest_education: Optional[str] = None
    years_experience: Optional[float] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class CandidateProfileUpdate(BaseModel):
    phone: Optional[str] = None
    location: Optional[str] = None
    highest_education: Optional[str] = None
    years_experience: Optional[float] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class RecruiterProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recruiter_id: int
    user_id: int
    company_name: str
    designation: Optional[str] = None
    company_website: Optional[str] = None
    status: str = "pending"  # PHASE 3: pending | approved | rejected | suspended


class RecruiterAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recruiter_id: int
    user_id: int
    company_name: str
    status: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None
