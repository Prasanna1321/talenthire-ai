"""
app/models/aptitude.py
------------------------
Phase 5: 30-question MCQ aptitude test.
Belongs in: backend/app/models/aptitude.py
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Numeric, CHAR, func
from app.database import Base


class AptitudeQuestion(Base):
    __tablename__ = "aptitude_questions"

    question_id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(255), nullable=False)
    option_b = Column(String(255), nullable=False)
    option_c = Column(String(255), nullable=False)
    option_d = Column(String(255), nullable=False)
    correct_option = Column(CHAR(1), nullable=False)
    # server_default (not just default=) so the DDL itself carries the
    # default — matters here because our seed script inserts via raw SQL
    # that omits this column, relying on the DATABASE to fill it in.
    difficulty = Column(String(20), server_default="medium")


class AptitudeTest(Base):
    __tablename__ = "aptitude_tests"

    test_id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    session_id = Column(Integer, ForeignKey("interview_sessions.session_id", ondelete="CASCADE"))
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    score = Column(Integer, nullable=True)
    percentage = Column(Numeric(5, 2), nullable=True)


class AptitudeTestQuestion(Base):
    __tablename__ = "aptitude_test_questions"

    test_id = Column(Integer, ForeignKey("aptitude_tests.test_id", ondelete="CASCADE"), primary_key=True)
    question_id = Column(Integer, ForeignKey("aptitude_questions.question_id"), primary_key=True)
    position = Column(Integer, nullable=False)


class AptitudeAnswer(Base):
    __tablename__ = "aptitude_answers"

    answer_id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("aptitude_tests.test_id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("aptitude_questions.question_id"), nullable=False)
    selected_option = Column(CHAR(1), nullable=True)
    is_correct = Column(Boolean, nullable=True)
