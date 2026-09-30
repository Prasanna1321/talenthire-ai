"""
app/services/interview_service.py
------------------------------------
Business logic for the full mock-interview workflow: question generation,
session lifecycle, answer transcription/evaluation, and feedback.
Belongs in: backend/app/services/interview_service.py

Wires together:
  - ml/question_generator (Gemini)  -> Mock Interview / AI Question Generator
  - ml/speech_recognition (Whisper) -> Speech Recognition
  - ml/answer_evaluator (SBERT)     -> Answer Evaluation
  - ml/feedback_generator (Gemini)  -> AI Feedback
"""

import os
import sys
import uuid
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

ML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml"))
if ML_DIR not in sys.path:
    sys.path.append(ML_DIR)

from app.config import settings
from app.models.interview import InterviewQuestion, InterviewSession, Answer, Score, Feedback
from app.models.job import Job


# ---------------------------------------------------------------------------
# Lazy ML imports (see resume_service.py for the rationale: this keeps the
# API bootable and the non-ML endpoints testable without requiring Gemini,
# Whisper, and sentence-transformers to be installed/configured up front).
# ---------------------------------------------------------------------------
def _get_question_generator():
    from question_generator.gemini_question_gen import GeminiQuestionGenerator
    return GeminiQuestionGenerator(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)


def _get_transcriber():
    from speech_recognition.whisper_transcriber import get_transcriber
    return get_transcriber()


def _get_answer_evaluator():
    from answer_evaluator.evaluator import get_answer_evaluator
    return get_answer_evaluator()


def _get_feedback_generator():
    from feedback_generator.gemini_feedback_gen import GeminiFeedbackGenerator
    return GeminiFeedbackGenerator(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)

# ---------------------------------------------------------------------------
# AI Question Generator
# ---------------------------------------------------------------------------
def generate_and_store_questions(
    db: Session,
    job_id: Optional[int],
    job_role: str,
    skills: Optional[List[str]] = None,
    num_questions: int = 5,
    difficulty: str = "mixed",
) -> List[InterviewQuestion]:
    generator = _get_question_generator()
    generated = generator.generate(
        job_role=job_role,
        skills=skills,
        job_description="",
        num_questions=num_questions,
        difficulty=difficulty,
    )

    questions = []
    for g in generated:
        q = InterviewQuestion(
            job_id=job_id,
            question_text=g.question_text,
            question_type=g.question_type,
            difficulty=g.difficulty,
            ideal_answer=g.ideal_answer,
            generated_by="gemini",
        )
        db.add(q)
        questions.append(q)

    db.commit()
    for q in questions:
        db.refresh(q)
    return questions


# ---------------------------------------------------------------------------
# Mock Interview session lifecycle
# ---------------------------------------------------------------------------
def start_session(db: Session, candidate_id: int, job_id: Optional[int], application_id: Optional[int], session_type: str) -> InterviewSession:
    session = InterviewSession(
        candidate_id=candidate_id,
        job_id=job_id,
        application_id=application_id,
        session_type=session_type,
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def complete_session(db: Session, session: InterviewSession) -> InterviewSession:
    from datetime import datetime, timezone

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


# ---------------------------------------------------------------------------
# Speech Recognition + Answer submission
# ---------------------------------------------------------------------------
def save_audio_file(upload: UploadFile, session_id: int) -> str:
    os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(upload.filename)[1] or ".wav"
    unique_name = f"session_{session_id}_{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(settings.AUDIO_UPLOAD_DIR, unique_name)
    with open(dest_path, "wb") as f:
        f.write(upload.file.read())
    return dest_path


def submit_audio_answer(db: Session, session_id: int, question_id: int, upload: UploadFile) -> Answer:
    """Save audio, transcribe with Whisper, store transcribed_text on the Answer row."""
    audio_path = save_audio_file(upload, session_id)
    transcriber = _get_transcriber()
    transcription = transcriber.transcribe(audio_path)

    answer = Answer(
        session_id=session_id,
        question_id=question_id,
        audio_file_path=audio_path,
        transcribed_text=transcription.text,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def submit_text_answer(db: Session, session_id: int, question_id: int, transcribed_text: str) -> Answer:
    """Fallback path when the candidate types instead of speaking."""
    answer = Answer(session_id=session_id, question_id=question_id, transcribed_text=transcribed_text)
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


# ---------------------------------------------------------------------------
# Answer Evaluation
# ---------------------------------------------------------------------------
def evaluate_answer(db: Session, answer: Answer, question: InterviewQuestion) -> Score:
    evaluator = _get_answer_evaluator()
    result = evaluator.evaluate(answer.transcribed_text or "", question.ideal_answer or "")

    score = Score(
        answer_id=answer.answer_id,
        similarity_score=result.similarity_score,
        relevance_score=result.relevance_score,
        fluency_score=result.fluency_score,
        confidence_score=result.confidence_score,
        final_score=result.final_score,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


# ---------------------------------------------------------------------------
# AI Feedback
# ---------------------------------------------------------------------------
def generate_session_feedback(db: Session, session: InterviewSession, visual_metrics: Optional[dict] = None) -> Feedback:
    import json

    answers = db.query(Answer).filter(Answer.session_id == session.session_id).all()

    qa_pairs = []
    for ans in answers:
        question = db.query(InterviewQuestion).filter(InterviewQuestion.question_id == ans.question_id).first()
        score = db.query(Score).filter(Score.answer_id == ans.answer_id).first()
        qa_pairs.append({
            "question": question.question_text if question else "",
            "answer": ans.transcribed_text or "",
            "final_score": float(score.final_score) if score and score.final_score is not None else 0.0,
        })

    generator = _get_feedback_generator()
    result = generator.generate(qa_pairs)

    visual_json = json.dumps(visual_metrics) if visual_metrics else None

    feedback = Feedback(
        session_id=session.session_id,
        strengths=result.strengths,
        areas_to_improve=result.areas_to_improve,
        detailed_feedback=result.detailed_feedback,
        overall_rating=result.overall_rating,
        visual_metrics=visual_json,
        generated_by="gemini",
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
