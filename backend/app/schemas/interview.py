"""
app/schemas/interview.py
--------------------------
Pydantic request/response models covering the full mock-interview workflow:
question generation -> session -> answer submission -> scoring -> feedback.
Belongs in: backend/app/schemas/interview.py
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class QuestionGenerateRequest(BaseModel):
    job_id: Optional[int] = None
    job_role: Optional[str] = None          # free-text role if no job_id (e.g. "Gen AI Engineer")
    num_questions: int = 5
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "mixed"


class InterviewQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    job_id: Optional[int] = None
    question_text: str
    question_type: str
    difficulty: str


class SessionStartRequest(BaseModel):
    job_id: Optional[int] = None
    application_id: Optional[int] = None
    session_type: Literal["mock", "official"] = "mock"


class InterviewSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: int
    candidate_id: int
    job_id: Optional[int] = None
    session_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None


class AnswerSubmitText(BaseModel):
    """Used when the candidate types an answer instead of speaking it."""
    session_id: int
    question_id: int
    transcribed_text: str


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer_id: int
    session_id: int
    question_id: int
    transcribed_text: Optional[str] = None
    answered_at: datetime


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score_id: int
    answer_id: int
    similarity_score: Optional[float] = None
    relevance_score: Optional[float] = None
    fluency_score: Optional[float] = None
    confidence_score: Optional[float] = None
    final_score: Optional[float] = None


class VisualMetricsOut(BaseModel):
    face_visibility: Optional[float] = None
    camera_orientation: Optional[float] = None
    posture_consistency: Optional[float] = None


class AptitudeSummaryOut(BaseModel):
    test_id: int
    score: Optional[int] = None
    percentage: Optional[float] = None
    total_questions: int = 30
    completed_at: Optional[datetime] = None


class SessionCompletePayload(BaseModel):
    visual_metrics: Optional[VisualMetricsOut] = None


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feedback_id: int
    session_id: int
    strengths: Optional[str] = None
    areas_to_improve: Optional[str] = None
    detailed_feedback: Optional[str] = None
    overall_rating: Optional[float] = None


class InterviewReportOut(BaseModel):
    """Aggregated report combining session + all answers + scores + feedback + aptitude + visual metrics."""
    session: InterviewSessionOut
    answers: list[AnswerOut]
    scores: list[ScoreOut]
    feedback: Optional[FeedbackOut] = None
    average_score: Optional[float] = None
    aptitude: Optional[AptitudeSummaryOut] = None
    visual_metrics: Optional[VisualMetricsOut] = None

