"""
app/services/recommendation_service.py
-----------------------------------------
Job Recommendation Module logic. Belongs in: backend/app/services/recommendation_service.py

Ranks open jobs against a candidate's most recently parsed resume using
the skill-overlap match score computed in resume_service.
"""

from typing import List

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.resume import Resume
from app.schemas.resume import JobRecommendation
from app.services.resume_service import compute_skill_match_score


def recommend_jobs_for_candidate(db: Session, candidate_id: int, top_n: int = 10) -> List[JobRecommendation]:
    latest_resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate_id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    if latest_resume is None:
        return []

    open_jobs = db.query(Job).filter(Job.status == "open").all()

    recommendations = []
    for job in open_jobs:
        score = compute_skill_match_score(latest_resume.extracted_skills or [], job.required_skills or [])
        if score <= 0:
            continue
        matched = sorted(
            set(s.lower() for s in (latest_resume.extracted_skills or []))
            & set(s.lower() for s in (job.required_skills or []))
        )
        recommendations.append(
            JobRecommendation(
                job_id=job.job_id,
                title=job.title,
                company_name=job.recruiter.company_name if job.recruiter else "",
                match_score=score,
                matched_skills=matched,
            )
        )

    recommendations.sort(key=lambda r: r.match_score, reverse=True)
    return recommendations[:top_n]
