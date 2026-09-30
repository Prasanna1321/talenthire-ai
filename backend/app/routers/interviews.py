"""
app/routers/interviews.py
----------------------------
AI Question Generator, Mock Interview, Speech Recognition, Answer
Evaluation, AI Feedback, and Interview Reports modules.
Belongs in: backend/app/routers/interviews.py

Endpoints:
    POST /api/interviews/questions/generate         (recruiter/admin) generate + store questions for a job
    GET  /api/interviews/questions/job/{job_id}      list questions for a job
    POST /api/interviews/sessions/start              (candidate) start a mock/official session
    POST /api/interviews/sessions/{id}/answer/audio   (candidate) submit spoken answer (Whisper)
    POST /api/interviews/sessions/{id}/answer/text    (candidate) submit typed answer
    POST /api/interviews/sessions/{id}/complete       (candidate) end session + generate feedback
    GET  /api/interviews/sessions/{id}/report         full report: answers + scores + feedback
    GET  /api/interviews/sessions/mine                (candidate) my session history
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Response
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.models.profile import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.interview import InterviewQuestion, InterviewSession, Answer, Score
from app.services.pdf_service import generate_interview_report_pdf
from app.schemas.interview import (
    QuestionGenerateRequest,
    InterviewQuestionOut,
    SessionStartRequest,
    InterviewSessionOut,
    AnswerSubmitText,
    AnswerOut,
    ScoreOut,
    FeedbackOut,
    InterviewReportOut,
    SessionCompletePayload,
)
from app.services.interview_service import (
    generate_and_store_questions,
    start_session,
    complete_session,
    submit_audio_answer,
    submit_text_answer,
    evaluate_answer,
    generate_session_feedback,
)

router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


# ---------------------------------------------------------------------------
# AI Question Generator
# ---------------------------------------------------------------------------
@router.post("/questions/generate", response_model=List[InterviewQuestionOut])
def generate_questions(
    payload: QuestionGenerateRequest,
    current_user: User = Depends(require_role("recruiter", "admin")),
    db: Session = Depends(get_db),
):
    job_role = payload.job_role
    skills = None
    if payload.job_id:
        job = db.query(Job).filter(Job.job_id == payload.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        job_role = job.title
        skills = job.required_skills

    if not job_role:
        raise HTTPException(status_code=400, detail="Provide either job_id or job_role")

    return generate_and_store_questions(
        db, payload.job_id, job_role, skills, payload.num_questions, payload.difficulty
    )


@router.get("/questions/job/{job_id}", response_model=List[InterviewQuestionOut])
def list_questions_for_job(job_id: int, db: Session = Depends(get_db)):
    return db.query(InterviewQuestion).filter(InterviewQuestion.job_id == job_id).all()


# ---------------------------------------------------------------------------
# Mock Interview session lifecycle
# ---------------------------------------------------------------------------
@router.post("/sessions/start", response_model=InterviewSessionOut, status_code=201)
def start_interview_session(
    payload: SessionStartRequest,
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    # PHASE 5 GATE: enforced here in the backend, not just hidden in the UI —
    # a candidate cannot start a mock interview without first completing the
    # 30-question aptitude test at least once.
    from app.models.aptitude import AptitudeTest
    completed_test = (
        db.query(AptitudeTest)
        .filter(AptitudeTest.candidate_id == candidate.candidate_id, AptitudeTest.completed_at.isnot(None))
        .first()
    )
    if not completed_test:
        raise HTTPException(
            status_code=403,
            detail="Please complete the 30-question aptitude test before starting a mock interview.",
        )

    return start_session(db, candidate.candidate_id, payload.job_id, payload.application_id, payload.session_type)


@router.get("/sessions/mine", response_model=List[InterviewSessionOut])
def my_sessions(
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return (
        db.query(InterviewSession)
        .filter(InterviewSession.candidate_id == candidate.candidate_id)
        .order_by(InterviewSession.started_at.desc())
        .all()
    )


def _get_owned_session(session_id: int, current_user: User, db: Session) -> InterviewSession:
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
    if not session or session.candidate_id != candidate.candidate_id:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return session


# ---------------------------------------------------------------------------
# Speech Recognition + Answer Evaluation (audio path)
# ---------------------------------------------------------------------------
@router.post("/sessions/{session_id}/answer/audio", response_model=ScoreOut)
def submit_answer_audio(
    session_id: int,
    question_id: int,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    session = _get_owned_session(session_id, current_user, db)
    question = db.query(InterviewQuestion).filter(InterviewQuestion.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = submit_audio_answer(db, session.session_id, question_id, audio_file)
    score = evaluate_answer(db, answer, question)
    return score


# ---------------------------------------------------------------------------
# Answer Evaluation (typed-text fallback path)
# ---------------------------------------------------------------------------
@router.post("/sessions/{session_id}/answer/text", response_model=ScoreOut)
def submit_answer_text(
    session_id: int,
    payload: AnswerSubmitText,
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    session = _get_owned_session(session_id, current_user, db)
    question = db.query(InterviewQuestion).filter(InterviewQuestion.question_id == payload.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = submit_text_answer(db, session.session_id, payload.question_id, payload.transcribed_text)
    score = evaluate_answer(db, answer, question)
    return score


# ---------------------------------------------------------------------------
# Complete session + AI Feedback
# ---------------------------------------------------------------------------
@router.post("/sessions/{session_id}/complete", response_model=FeedbackOut)
def complete_interview_session(
    session_id: int,
    payload: Optional[SessionCompletePayload] = None,
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    session = _get_owned_session(session_id, current_user, db)
    session = complete_session(db, session)
    v_dict = payload.visual_metrics.model_dump() if (payload and payload.visual_metrics) else None
    feedback = generate_session_feedback(db, session, visual_metrics=v_dict)
    return feedback


# ---------------------------------------------------------------------------
# Interview Reports
# ---------------------------------------------------------------------------
@router.get("/sessions/{session_id}/report", response_model=InterviewReportOut)
def get_interview_report(
    session_id: int,
    current_user: User = Depends(require_role("candidate", "recruiter", "admin")),
    db: Session = Depends(get_db),
):
    import json
    session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    answers = db.query(Answer).filter(Answer.session_id == session_id).all()
    scores = [db.query(Score).filter(Score.answer_id == a.answer_id).first() for a in answers]
    scores = [s for s in scores if s is not None]
    feedback = session.feedback

    avg_score = round(sum(float(s.final_score) for s in scores) / len(scores), 2) if scores else None

    from app.models.aptitude import AptitudeTest
    aptitude_test = (
        db.query(AptitudeTest)
        .filter(AptitudeTest.candidate_id == session.candidate_id, AptitudeTest.completed_at.isnot(None))
        .order_by(AptitudeTest.completed_at.desc())
        .first()
    )
    aptitude_out = None
    if aptitude_test:
        from app.schemas.interview import AptitudeSummaryOut
        aptitude_out = AptitudeSummaryOut(
            test_id=aptitude_test.test_id,
            score=aptitude_test.score,
            percentage=float(aptitude_test.percentage) if aptitude_test.percentage is not None else None,
            total_questions=30,
            completed_at=aptitude_test.completed_at,
        )

    visual_out = None
    if feedback and feedback.visual_metrics:
        try:
            v_data = json.loads(feedback.visual_metrics)
            from app.schemas.interview import VisualMetricsOut
            visual_out = VisualMetricsOut(**v_data)
        except Exception:
            pass

    return InterviewReportOut(
        session=session,
        answers=answers,
        scores=scores,
        feedback=feedback,
        average_score=avg_score,
        aptitude=aptitude_out,
        visual_metrics=visual_out,
    )


@router.get("/sessions/{session_id}/report/pdf")
def download_interview_report_pdf(
    session_id: int,
    current_user: User = Depends(require_role("candidate", "recruiter", "admin")),
    db: Session = Depends(get_db),
):
    """PHASE 7: generates and streams a branded PDF version of the interview report."""
    session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    candidate = db.query(Candidate).filter(Candidate.candidate_id == session.candidate_id).first()
    candidate_user = db.query(User).filter(User.user_id == candidate.user_id).first() if candidate else None
    candidate_name = candidate_user.full_name if candidate_user else "Candidate"

    job = db.query(Job).filter(Job.job_id == session.job_id).first() if session.job_id else None

    latest_resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == session.candidate_id, Resume.is_current.is_(True))
        .first()
        if candidate else None
    )

    answers = db.query(Answer).filter(Answer.session_id == session_id).all()
    question_scores = []
    all_scores = []
    for ans in answers:
        question = db.query(InterviewQuestion).filter(InterviewQuestion.question_id == ans.question_id).first()
        score = db.query(Score).filter(Score.answer_id == ans.answer_id).first()
        if score and score.final_score is not None:
            all_scores.append(float(score.final_score))
        question_scores.append({
            "question": question.question_text if question else "",
            "final_score": float(score.final_score) if score and score.final_score is not None else 0.0,
        })
    avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else None

    feedback = None
    if session.feedback:
        feedback = {
            "strengths": session.feedback.strengths,
            "areas_to_improve": session.feedback.areas_to_improve,
            "detailed_feedback": session.feedback.detailed_feedback,
            "overall_rating": float(session.feedback.overall_rating) if session.feedback.overall_rating is not None else None,
        }

    from app.models.aptitude import AptitudeTest
    latest_aptitude_test = (
        db.query(AptitudeTest)
        .filter(AptitudeTest.candidate_id == session.candidate_id, AptitudeTest.completed_at.isnot(None))
        .order_by(AptitudeTest.completed_at.desc())
        .first()
    )

    visual_metrics_data = None
    if session.feedback and session.feedback.visual_metrics:
        try:
            import json
            visual_metrics_data = json.loads(session.feedback.visual_metrics)
        except Exception:
            pass

    pdf_bytes = generate_interview_report_pdf(
        candidate_name=candidate_name,
        job_title=job.title if job else None,
        ats_score=float(latest_resume.ats_score) if latest_resume and latest_resume.ats_score is not None else None,
        aptitude_percentage=float(latest_aptitude_test.percentage) if latest_aptitude_test and latest_aptitude_test.percentage is not None else None,
        average_interview_score=avg_score,
        question_scores=question_scores,
        feedback=feedback,
        visual_metrics=visual_metrics_data,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="talenthire_report_session_{session_id}.pdf"'},
    )
