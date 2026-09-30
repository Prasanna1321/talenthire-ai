"""
app/routers/users.py
---------------------
Candidate Dashboard + Recruiter Dashboard (profile & summary data).
Belongs in: backend/app/routers/users.py

Endpoints:
    GET  /api/users/me
    GET  /api/users/candidate/profile
    PUT  /api/users/candidate/profile
    GET  /api/users/candidate/dashboard
    GET  /api/users/recruiter/profile
    GET  /api/users/recruiter/dashboard
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.user import User
from app.models.profile import Candidate, Recruiter
from app.models.job import Application, Job
from app.models.resume import Resume
from app.models.interview import InterviewSession
from app.schemas.user import UserOut, CandidateProfileOut, CandidateProfileUpdate, RecruiterProfileOut

router = APIRouter(prefix="/api/users", tags=["Users & Dashboards"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------------------------------------------------------------------------
# Candidate profile & dashboard
# ---------------------------------------------------------------------------
@router.get("/candidate/profile", response_model=CandidateProfileOut)
def get_candidate_profile(
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    profile = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return profile


@router.put("/candidate/profile", response_model=CandidateProfileOut)
def update_candidate_profile(
    payload: CandidateProfileUpdate,
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    profile = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/candidate/dashboard")
def candidate_dashboard(
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    """Aggregated summary cards for the Candidate Dashboard UI."""
    profile = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    total_applications = db.query(Application).filter(Application.candidate_id == profile.candidate_id).count()
    total_resumes = db.query(Resume).filter(Resume.candidate_id == profile.candidate_id).count()
    total_interviews = db.query(InterviewSession).filter(InterviewSession.candidate_id == profile.candidate_id).count()
    completed_interviews = (
        db.query(InterviewSession)
        .filter(InterviewSession.candidate_id == profile.candidate_id, InterviewSession.status == "completed")
        .count()
    )

    return {
        "full_name": current_user.full_name,
        "total_applications": total_applications,
        "total_resumes_uploaded": total_resumes,
        "total_interviews_taken": total_interviews,
        "completed_interviews": completed_interviews,
    }


# ---------------------------------------------------------------------------
# Recruiter profile & dashboard
# ---------------------------------------------------------------------------
@router.get("/recruiter/profile", response_model=RecruiterProfileOut)
def get_recruiter_profile(
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db),
):
    profile = db.query(Recruiter).filter(Recruiter.user_id == current_user.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")
    return profile


@router.get("/recruiter/dashboard")
def recruiter_dashboard(
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db),
):
    """Aggregated summary cards for the Recruiter Dashboard UI."""
    profile = db.query(Recruiter).filter(Recruiter.user_id == current_user.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

    total_jobs = db.query(Job).filter(Job.recruiter_id == profile.recruiter_id).count()
    open_jobs = db.query(Job).filter(Job.recruiter_id == profile.recruiter_id, Job.status == "open").count()

    job_ids = [j.job_id for j in db.query(Job.job_id).filter(Job.recruiter_id == profile.recruiter_id).all()]
    total_applications = db.query(Application).filter(Application.job_id.in_(job_ids)).count() if job_ids else 0
    shortlisted = (
        db.query(Application)
        .filter(Application.job_id.in_(job_ids), Application.status == "shortlisted")
        .count()
        if job_ids else 0
    )

    return {
        "company_name": profile.company_name,
        "total_jobs_posted": total_jobs,
        "open_jobs": open_jobs,
        "total_applications_received": total_applications,
        "shortlisted_candidates": shortlisted,
    }
