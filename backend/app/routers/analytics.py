"""
app/routers/analytics.py
---------------------------
Recruiter Analytics Module. Belongs in: backend/app/routers/analytics.py

Endpoints:
    GET /api/analytics/recruiter    (recruiter) aggregate hiring analytics
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.models.profile import Recruiter
from app.models.job import Job, Application
from app.models.interview import InterviewSession, Score, Answer
from app.schemas.notification import RecruiterAnalyticsOut

router = APIRouter(prefix="/api/analytics", tags=["Recruiter Analytics"])


@router.get("/recruiter", response_model=RecruiterAnalyticsOut)
def recruiter_analytics(
    current_user: User = Depends(require_role("recruiter")),
    db: Session = Depends(get_db),
):
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.user_id).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

    job_ids = [j.job_id for j in db.query(Job.job_id).filter(Job.recruiter_id == recruiter.recruiter_id).all()]

    total_jobs_posted = len(job_ids)
    total_applications = db.query(Application).filter(Application.job_id.in_(job_ids)).count() if job_ids else 0
    total_interviews = (
        db.query(InterviewSession).filter(InterviewSession.job_id.in_(job_ids)).count() if job_ids else 0
    )

    # Average final_score across all answers tied to this recruiter's jobs
    session_ids = [
        s.session_id
        for s in db.query(InterviewSession.session_id).filter(InterviewSession.job_id.in_(job_ids)).all()
    ] if job_ids else []

    avg_score = None
    if session_ids:
        answer_ids = [
            a.answer_id for a in db.query(Answer.answer_id).filter(Answer.session_id.in_(session_ids)).all()
        ]
        if answer_ids:
            scores = db.query(Score).filter(Score.answer_id.in_(answer_ids)).all()
            valid_scores = [float(s.final_score) for s in scores if s.final_score is not None]
            if valid_scores:
                avg_score = round(sum(valid_scores) / len(valid_scores), 2)

    # Most commonly required skills across this recruiter's job postings
    skill_counts: dict[str, int] = {}
    jobs = db.query(Job).filter(Job.recruiter_id == recruiter.recruiter_id).all()
    for job in jobs:
        for skill in (job.required_skills or []):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    top_skills = sorted(skill_counts, key=skill_counts.get, reverse=True)[:10]

    return RecruiterAnalyticsOut(
        total_jobs_posted=total_jobs_posted,
        total_applications=total_applications,
        total_interviews_conducted=total_interviews,
        average_candidate_score=avg_score,
        top_matched_skills=top_skills,
    )
