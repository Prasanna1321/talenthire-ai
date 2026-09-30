"""
app/models/interview.py
------------------------
ORM models for the entire mock/official interview workflow:
InterviewQuestion -> InterviewSession -> Answer -> Score -> Feedback.
Belongs in: backend/app/models/interview.py
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    question_id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.job_id", ondelete="CASCADE"))
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), default="technical")  # technical | behavioral | situational | coding
    difficulty = Column(String(20), default="medium")
    ideal_answer = Column(Text)  # reference answer used for cosine-similarity scoring
    generated_by = Column(String(20), default="gemini")
    created_at = Column(DateTime, server_default=func.now())

    job = relationship("Job", back_populates="questions")
    answers = relationship("Answer", back_populates="question")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.application_id", ondelete="CASCADE"))
    candidate_id = Column(Integer, ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.job_id", ondelete="SET NULL"))
    session_type = Column(String(20), default="mock")  # mock | official
    mode = Column(String(20), default="text")  # PHASE 6: text | audio_upload | realtime_voice
    status = Column(String(20), default="in_progress")  # in_progress | completed | abandoned
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    candidate = relationship("Candidate", back_populates="interview_sessions")
    application = relationship("Application", back_populates="interview_sessions")
    answers = relationship("Answer", back_populates="session", cascade="all, delete")
    feedback = relationship("Feedback", back_populates="session", uselist=False, cascade="all, delete")


class Answer(Base):
    __tablename__ = "answers"

    answer_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.session_id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("interview_questions.question_id", ondelete="CASCADE"), nullable=False)
    audio_file_path = Column(String(255))
    transcribed_text = Column(Text)  # Whisper output
    answered_at = Column(DateTime, server_default=func.now())

    session = relationship("InterviewSession", back_populates="answers")
    question = relationship("InterviewQuestion", back_populates="answers")
    score = relationship("Score", back_populates="answer", uselist=False, cascade="all, delete")


class Score(Base):
    __tablename__ = "scores"

    score_id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.answer_id", ondelete="CASCADE"), unique=True, nullable=False)
    similarity_score = Column(Numeric(5, 4))   # cosine similarity vs ideal_answer embedding
    relevance_score = Column(Numeric(5, 2))    # 0-100
    fluency_score = Column(Numeric(5, 2))      # 0-100
    confidence_score = Column(Numeric(5, 2))   # 0-100
    final_score = Column(Numeric(5, 2))        # weighted aggregate
    evaluated_at = Column(DateTime, server_default=func.now())

    answer = relationship("Answer", back_populates="score")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.session_id", ondelete="CASCADE"), unique=True, nullable=False)
    strengths = Column(Text)
    areas_to_improve = Column(Text)
    detailed_feedback = Column(Text)
    overall_rating = Column(Numeric(3, 1))  # 0-10
    visual_metrics = Column(Text, nullable=True)  # JSON string of observable visual indicators
    generated_by = Column(String(20), default="gemini")
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("InterviewSession", back_populates="feedback")
