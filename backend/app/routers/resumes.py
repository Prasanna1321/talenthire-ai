"""
app/routers/resumes.py
------------------------
Resume Upload, Resume Parser, Resume Classification, Skill Extraction,
Job Recommendation, and (Phase 4) versioning/ATS scoring/consistency checks.
Belongs in: backend/app/routers/resumes.py

Endpoints:
    POST /api/resumes/upload?force=false     (candidate) upload -> parse -> ATS score -> new version
    GET  /api/resumes/mine                   (candidate) current resume + all past versions
    GET  /api/resumes/history                (candidate) explicit version history (same data, clearer name)
    GET  /api/resumes/{resume_id}            get a single resume version's data
    GET  /api/resumes/recommendations/jobs   (candidate) AI job recommendations
"""

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.models.profile import Candidate
from app.models.resume import Resume
from app.schemas.resume import ResumeOut, ResumeUploadResponse, JobRecommendation
from app.services.resume_service import process_resume
from app.services.recommendation_service import recommend_jobs_for_candidate

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=201)
def upload_resume(
    file: UploadFile = File(...),
    force: bool = Query(default=False, description="Set true to proceed despite an identity-consistency warning"),
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    result = process_resume(db, candidate.candidate_id, file, force=force)
    return ResumeUploadResponse(**result)


@router.get("/mine", response_model=List[ResumeOut])
def list_my_resumes(
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate.candidate_id)
        .order_by(Resume.version_number.desc())
        .all()
    )


@router.get("/history", response_model=List[ResumeOut])
def resume_history(
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    """Same data as /mine — explicit name for the Resume History UI (Phase 4)."""
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate.candidate_id)
        .order_by(Resume.version_number.desc())
        .all()
    )


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    resume_id: int,
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
    if not resume or resume.candidate_id != candidate.candidate_id:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.get("/recommendations/jobs", response_model=List[JobRecommendation])
def get_job_recommendations(
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return recommend_jobs_for_candidate(db, candidate.candidate_id)
