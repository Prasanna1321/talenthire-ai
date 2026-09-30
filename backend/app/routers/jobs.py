"""
app/routers/jobs.py
--------------------
Job posting and browsing. Belongs in: backend/app/routers/jobs.py

Endpoints:
    POST   /api/jobs                 (recruiter) create a job
    GET    /api/jobs                 (any authenticated user) list/browse open jobs
    GET    /api/jobs/{job_id}        get a single job
    PUT    /api/jobs/{job_id}        (recruiter, owner) update a job
    DELETE /api/jobs/{job_id}        (recruiter, owner) close/delete a job
    GET    /api/jobs/recruiter/mine  (recruiter) list jobs I posted
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role, require_approved_recruiter
from app.database import get_db
from app.models.user import User
from app.models.profile import Recruiter
from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate, JobOut

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


def _get_recruiter_profile(current_user: User, db: Session) -> Recruiter:
    profile = db.query(Recruiter).filter(Recruiter.user_id == current_user.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")
    return profile


@router.post("", response_model=JobOut, status_code=201)
def create_job(
    payload: JobCreate,
    current_user: User = Depends(require_approved_recruiter),
    db: Session = Depends(get_db),
):
    recruiter = _get_recruiter_profile(current_user, db)
    job = Job(recruiter_id=recruiter.recruiter_id, **payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=List[JobOut])
def list_jobs(
    status_filter: Optional[str] = Query(default="open", alias="status"),
    location: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Job)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    return query.order_by(Job.created_at.desc()).all()


@router.get("/recruiter/mine", response_model=List[JobOut])
def list_my_jobs(
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db),
):
    recruiter = _get_recruiter_profile(current_user, db)
    return db.query(Job).filter(Job.recruiter_id == recruiter.recruiter_id).order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobOut)
def update_job(
    job_id: int,
    payload: JobUpdate,
    current_user: User = Depends(require_approved_recruiter),
    db: Session = Depends(get_db),
):
    recruiter = _get_recruiter_profile(current_user, db)
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.recruiter_id != recruiter.recruiter_id:
        raise HTTPException(status_code=403, detail="You do not own this job posting")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=204)
def delete_job(
    job_id: int,
    current_user: User = Depends(require_approved_recruiter),
    db: Session = Depends(get_db),
):
    recruiter = _get_recruiter_profile(current_user, db)
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.recruiter_id != recruiter.recruiter_id:
        raise HTTPException(status_code=403, detail="You do not own this job posting")

    db.delete(job)
    db.commit()
