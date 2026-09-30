"""
app/routers/applications.py
-----------------------------
Candidate job applications + recruiter application review.
Belongs in: backend/app/routers/applications.py

Endpoints:
    POST /api/applications                    (candidate) apply to a job
    GET  /api/applications/candidate/mine      (candidate) my applications
    GET  /api/applications/job/{job_id}        (recruiter) applicants for a job
    PUT  /api/applications/{application_id}/status  (recruiter) update status
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.models.profile import Candidate, Recruiter
from app.models.job import Job, Application
from app.models.resume import Resume
from app.schemas.job import ApplicationCreate, ApplicationOut, ApplicationStatusUpdate, CandidateDetailOut
from app.services.resume_service import compute_skill_match_score

router = APIRouter(prefix="/api/applications", tags=["Applications"])


@router.post("", response_model=ApplicationOut, status_code=201)
def apply_to_job(
    payload: ApplicationCreate,
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    job = db.query(Job).filter(Job.job_id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = db.query(Application).filter(
        Application.candidate_id == candidate.candidate_id, Application.job_id == payload.job_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this job")

    match_score = 0.0
    resume_id = payload.resume_id
    if resume_id:
        resume = db.query(Resume).filter(Resume.resume_id == resume_id).first()
        if resume:
            match_score = compute_skill_match_score(resume.extracted_skills or [], job.required_skills or [])

    application = Application(
        candidate_id=candidate.candidate_id,
        job_id=payload.job_id,
        resume_id=resume_id,
        match_score=match_score,
        status="applied",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/candidate/mine", response_model=List[ApplicationOut])
def my_applications(
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return db.query(Application).filter(Application.candidate_id == candidate.candidate_id).all()


@router.get("/job/{job_id}", response_model=List[ApplicationOut])
def job_applicants(
    job_id: int,
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db),
):
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.user_id).first()
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.recruiter_id != recruiter.recruiter_id:
        raise HTTPException(status_code=403, detail="You do not own this job posting")

    return (
        db.query(Application)
        .filter(Application.job_id == job_id)
        .order_by(Application.match_score.desc())
        .all()
    )


@router.get("/job/{job_id}/candidates", response_model=List[CandidateDetailOut])
def job_candidates_detailed(
    job_id: int,
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db),
):
    """
    PHASE 8: one place to see, per applicant, their ATS score, aptitude
    score, interview score, and matched/missing skills against this job —
    not just a single match percentage.
    """
    from app.models.aptitude import AptitudeTest
    from app.models.interview import InterviewSession, Answer, Score

    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.user_id).first()
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.recruiter_id != recruiter.recruiter_id:
        raise HTTPException(status_code=403, detail="You do not own this job posting")

    applications = db.query(Application).filter(Application.job_id == job_id).all()
    job_skills_lower = {s.lower() for s in (job.required_skills or [])}

    results = []
    for app_row in applications:
        candidate = db.query(Candidate).filter(Candidate.candidate_id == app_row.candidate_id).first()
        user = db.query(User).filter(User.user_id == candidate.user_id).first() if candidate else None

        resume = db.query(Resume).filter(Resume.resume_id == app_row.resume_id).first() if app_row.resume_id else (
            db.query(Resume)
            .filter(Resume.candidate_id == app_row.candidate_id, Resume.is_current.is_(True))
            .first()
        )
        resume_skills_lower = {s.lower() for s in (resume.extracted_skills or [])} if resume else set()
        matched = sorted(resume_skills_lower & job_skills_lower)
        missing = sorted(job_skills_lower - resume_skills_lower)

        latest_test = (
            db.query(AptitudeTest)
            .filter(AptitudeTest.candidate_id == app_row.candidate_id, AptitudeTest.completed_at.isnot(None))
            .order_by(AptitudeTest.completed_at.desc())
            .first()
        )

        session_ids = [
            s.session_id for s in
            db.query(InterviewSession.session_id).filter(InterviewSession.candidate_id == app_row.candidate_id).all()
        ]
        interview_score = None
        if session_ids:
            answer_ids = [
                a.answer_id for a in db.query(Answer.answer_id).filter(Answer.session_id.in_(session_ids)).all()
            ]
            if answer_ids:
                scores = [
                    float(s.final_score) for s in db.query(Score).filter(Score.answer_id.in_(answer_ids)).all()
                    if s.final_score is not None
                ]
                if scores:
                    interview_score = round(sum(scores) / len(scores), 2)

        results.append(CandidateDetailOut(
            application_id=app_row.application_id,
            candidate_id=app_row.candidate_id,
            full_name=user.full_name if user else "Unknown",
            email=user.email if user else "",
            status=app_row.status,
            match_score=float(app_row.match_score) if app_row.match_score is not None else None,
            matched_skills=matched,
            missing_skills=missing,
            ats_score=float(resume.ats_score) if resume and resume.ats_score is not None else None,
            aptitude_percentage=float(latest_test.percentage) if latest_test and latest_test.percentage is not None else None,
            interview_score=interview_score,
        ))

    return results


@router.put("/{application_id}/status", response_model=ApplicationOut)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db),
):
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.user_id).first()
    application = db.query(Application).filter(Application.application_id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    job = db.query(Job).filter(Job.job_id == application.job_id).first()
    if job.recruiter_id != recruiter.recruiter_id:
        raise HTTPException(status_code=403, detail="You do not own this job posting")

    application.status = payload.status
    db.commit()
    db.refresh(application)
    return application
