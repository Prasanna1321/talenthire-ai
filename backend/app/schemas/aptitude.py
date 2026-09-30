"""
app/schemas/aptitude.py
--------------------------
Phase 5: 30-question MCQ aptitude test schemas.
Belongs in: backend/app/schemas/aptitude.py
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class AptitudeQuestionOut(BaseModel):
    """Question WITHOUT the correct answer — safe to send to the candidate mid-test."""
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    category: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    difficulty: str


class AptitudeTestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_id: int
    candidate_id: int
    started_at: str | None = None
    completed_at: str | None = None
    score: Optional[int] = None
    percentage: Optional[float] = None


class AptitudeStartResponse(BaseModel):
    test_id: int
    questions: List[AptitudeQuestionOut]


class AptitudeAnswerIn(BaseModel):
    question_id: int
    selected_option: str  # 'A' | 'B' | 'C' | 'D'


class AptitudeSubmitRequest(BaseModel):
    test_id: int
    answers: List[AptitudeAnswerIn]


class AptitudeResultOut(BaseModel):
    test_id: int
    score: int
    total_questions: int
    percentage: float
    completed_at: str
