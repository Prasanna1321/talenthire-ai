"""
app/models/__init__.py
-----------------------
Re-exports every ORM model so `from app.models import User, Job, ...` works,
and so Base.metadata sees every table for create_all(). Belongs in:
backend/app/models/__init__.py
"""

from app.models.user import User
from app.models.profile import Recruiter, Candidate
from app.models.job import Job, Application
from app.models.resume import Resume
from app.models.interview import (
    InterviewQuestion,
    InterviewSession,
    Answer,
    Score,
    Feedback,
)
from app.models.notification import Notification
from app.models.otp import EmailOTP
from app.models.aptitude import AptitudeQuestion, AptitudeTest, AptitudeTestQuestion, AptitudeAnswer

__all__ = [
    "User", "Recruiter", "Candidate", "Job", "Application", "Resume",
    "InterviewQuestion", "InterviewSession", "Answer", "Score", "Feedback",
    "Notification", "EmailOTP",
    "AptitudeQuestion", "AptitudeTest", "AptitudeTestQuestion", "AptitudeAnswer",
]
