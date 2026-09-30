"""
app/schemas/notification.py
-----------------------------
Pydantic response model for in-app notifications.
Belongs in: backend/app/schemas/notification.py
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: int
    title: str
    message: str
    is_read: bool
    notification_type: str
    created_at: datetime


class RecruiterAnalyticsOut(BaseModel):
    total_jobs_posted: int
    total_applications: int
    total_interviews_conducted: int
    average_candidate_score: Optional[float] = None
    top_matched_skills: list[str] = []
