"""
app/routers/admin.py
-----------------------
Admin Dashboard Module + Phase 3 recruiter approval workflow.
Belongs in: backend/app/routers/admin.py

Endpoints:
    GET  /api/admin/users                          list all users
    PUT  /api/admin/users/{id}/status               activate/deactivate a user
    GET  /api/admin/dashboard                       system-wide summary stats
    GET  /api/admin/recruiters?status=pending       list recruiters by status
    POST /api/admin/recruiters/{id}/approve
    POST /api/admin/recruiters/{id}/reject
    POST /api/admin/recruiters/{id}/suspend
    POST /api/admin/recruiters/{id}/activate
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.models.profile import Recruiter
from app.models.job import Job, Application
from app.models.resume import Resume
from app.models.interview import InterviewSession
from app.schemas.user import UserOut, RecruiterAdminOut
from app.services.email_service import send_recruiter_status_email

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserOut])
def list_all_users(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}/status", response_model=UserOut)
def set_user_active_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return {
        "total_users": db.query(User).count(),
        "total_candidates": db.query(User).filter(User.role == "candidate").count(),
        "total_recruiters": db.query(User).filter(User.role == "recruiter").count(),
        "total_jobs": db.query(Job).count(),
        "total_applications": db.query(Application).count(),
        "total_resumes_uploaded": db.query(Resume).count(),
        "total_interview_sessions": db.query(InterviewSession).count(),
    }


# ---------------------------------------------------------------------------
# PHASE 3: Recruiter approval workflow
# ---------------------------------------------------------------------------
def _recruiter_admin_view(db: Session, recruiter: Recruiter) -> RecruiterAdminOut:
    user = db.query(User).filter(User.user_id == recruiter.user_id).first()
    return RecruiterAdminOut(
        recruiter_id=recruiter.recruiter_id,
        user_id=recruiter.user_id,
        company_name=recruiter.company_name,
        status=recruiter.status,
        full_name=user.full_name if user else None,
        email=user.email if user else None,
        created_at=recruiter.created_at,
    )


@router.get("/recruiters", response_model=List[RecruiterAdminOut])
def list_recruiters(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(Recruiter)
    if status_filter:
        query = query.filter(Recruiter.status == status_filter)
    recruiters = query.order_by(Recruiter.created_at.desc()).all()
    return [_recruiter_admin_view(db, r) for r in recruiters]


def _update_recruiter_status(db: Session, recruiter_id: int, new_status: str, admin: User) -> RecruiterAdminOut:
    recruiter = db.query(Recruiter).filter(Recruiter.recruiter_id == recruiter_id).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")

    recruiter.status = new_status
    recruiter.approved_by = admin.user_id
    from datetime import datetime, timezone
    recruiter.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(recruiter)

    user = db.query(User).filter(User.user_id == recruiter.user_id).first()
    if user:
        send_recruiter_status_email(user.email, user.full_name, new_status if new_status != "approved" else "approved")

    return _recruiter_admin_view(db, recruiter)


@router.post("/recruiters/{recruiter_id}/approve", response_model=RecruiterAdminOut)
def approve_recruiter(recruiter_id: int, current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return _update_recruiter_status(db, recruiter_id, "approved", current_user)


@router.post("/recruiters/{recruiter_id}/reject", response_model=RecruiterAdminOut)
def reject_recruiter(recruiter_id: int, current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return _update_recruiter_status(db, recruiter_id, "rejected", current_user)


@router.post("/recruiters/{recruiter_id}/suspend", response_model=RecruiterAdminOut)
def suspend_recruiter(recruiter_id: int, current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return _update_recruiter_status(db, recruiter_id, "suspended", current_user)


@router.post("/recruiters/{recruiter_id}/activate", response_model=RecruiterAdminOut)
def activate_recruiter(recruiter_id: int, current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return _update_recruiter_status(db, recruiter_id, "approved", current_user)
