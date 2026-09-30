"""
app/routers/aptitude.py
--------------------------
Phase 5: 30-question MCQ aptitude test, taken before the mock interview.
Belongs in: backend/app/routers/aptitude.py

Endpoints:
    POST /api/aptitude/start              (candidate) start a new test, get 30 random questions (no answers)
    GET  /api/aptitude/questions?test_id= (candidate) re-fetch the SAME 30 questions for an in-progress test
    POST /api/aptitude/submit             (candidate) submit answers -> server-side grading
    GET  /api/aptitude/result?test_id=    (candidate) get the graded result
"""

import random

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.models.profile import Candidate
from app.models.aptitude import AptitudeQuestion, AptitudeTest, AptitudeTestQuestion, AptitudeAnswer
from app.schemas.aptitude import (
    AptitudeStartResponse, AptitudeQuestionOut, AptitudeSubmitRequest, AptitudeResultOut,
)

router = APIRouter(prefix="/api/aptitude", tags=["Aptitude Test"])

QUESTIONS_PER_TEST = 30


def _get_candidate(current_user: User, db: Session) -> Candidate:
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return candidate


@router.post("/start", response_model=AptitudeStartResponse, status_code=201)
def start_test(
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    candidate = _get_candidate(current_user, db)

    all_question_ids = [row.question_id for row in db.query(AptitudeQuestion.question_id).all()]
    if len(all_question_ids) < QUESTIONS_PER_TEST:
        raise HTTPException(
            status_code=500,
            detail=f"Question bank has only {len(all_question_ids)} questions; needs at least {QUESTIONS_PER_TEST}. Run database/seed_aptitude_questions.py.",
        )

    selected_ids = random.sample(all_question_ids, QUESTIONS_PER_TEST)

    test = AptitudeTest(candidate_id=candidate.candidate_id)
    db.add(test)
    db.flush()

    for position, question_id in enumerate(selected_ids):
        db.add(AptitudeTestQuestion(test_id=test.test_id, question_id=question_id, position=position))
    db.commit()
    db.refresh(test)

    questions = (
        db.query(AptitudeQuestion)
        .join(AptitudeTestQuestion, AptitudeTestQuestion.question_id == AptitudeQuestion.question_id)
        .filter(AptitudeTestQuestion.test_id == test.test_id)
        .order_by(AptitudeTestQuestion.position)
        .all()
    )

    return AptitudeStartResponse(
        test_id=test.test_id,
        questions=[AptitudeQuestionOut.model_validate(q) for q in questions],
    )


@router.get("/questions", response_model=AptitudeStartResponse)
def get_test_questions(
    test_id: int = Query(...),
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    """Re-fetches the SAME 30 questions for an in-progress test (idempotent on page refresh)."""
    candidate = _get_candidate(current_user, db)
    test = db.query(AptitudeTest).filter(AptitudeTest.test_id == test_id).first()
    if not test or test.candidate_id != candidate.candidate_id:
        raise HTTPException(status_code=404, detail="Aptitude test not found")

    questions = (
        db.query(AptitudeQuestion)
        .join(AptitudeTestQuestion, AptitudeTestQuestion.question_id == AptitudeQuestion.question_id)
        .filter(AptitudeTestQuestion.test_id == test_id)
        .order_by(AptitudeTestQuestion.position)
        .all()
    )
    return AptitudeStartResponse(test_id=test_id, questions=[AptitudeQuestionOut.model_validate(q) for q in questions])


@router.post("/submit", response_model=AptitudeResultOut)
def submit_test(
    payload: AptitudeSubmitRequest,
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    """
    Grades server-side ONLY — the correct_option is never sent to the
    frontend before this point, and the client's own claim of correctness
    (if any) is ignored entirely; we look up correct_option from the DB.
    """
    candidate = _get_candidate(current_user, db)
    test = db.query(AptitudeTest).filter(AptitudeTest.test_id == payload.test_id).first()
    if not test or test.candidate_id != candidate.candidate_id:
        raise HTTPException(status_code=404, detail="Aptitude test not found")
    if test.completed_at is not None:
        raise HTTPException(status_code=400, detail="This test has already been submitted")

    valid_question_ids = {
        row.question_id
        for row in db.query(AptitudeTestQuestion.question_id).filter(AptitudeTestQuestion.test_id == test.test_id).all()
    }

    correct_count = 0
    total = len(valid_question_ids)
    answered_ids = set()

    for answer in payload.answers:
        if answer.question_id not in valid_question_ids:
            continue  # ignore answers for questions not part of this test
        answered_ids.add(answer.question_id)
        question = db.query(AptitudeQuestion).filter(AptitudeQuestion.question_id == answer.question_id).first()
        is_correct = bool(question and answer.selected_option.upper() == question.correct_option)
        if is_correct:
            correct_count += 1
        db.add(AptitudeAnswer(
            test_id=test.test_id,
            question_id=answer.question_id,
            selected_option=answer.selected_option.upper(),
            is_correct=is_correct,
        ))

    from datetime import datetime, timezone
    test.score = correct_count
    test.percentage = round((correct_count / total) * 100, 2) if total else 0.0
    test.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(test)

    return AptitudeResultOut(
        test_id=test.test_id,
        score=test.score,
        total_questions=total,
        percentage=float(test.percentage),
        completed_at=test.completed_at.isoformat(),
    )


@router.get("/result", response_model=AptitudeResultOut)
def get_result(
    test_id: int = Query(...),
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    candidate = _get_candidate(current_user, db)
    test = db.query(AptitudeTest).filter(AptitudeTest.test_id == test_id).first()
    if not test or test.candidate_id != candidate.candidate_id:
        raise HTTPException(status_code=404, detail="Aptitude test not found")
    if test.completed_at is None:
        raise HTTPException(status_code=400, detail="This test has not been completed yet")

    total = db.query(AptitudeTestQuestion).filter(AptitudeTestQuestion.test_id == test_id).count()
    return AptitudeResultOut(
        test_id=test.test_id,
        score=test.score,
        total_questions=total,
        percentage=float(test.percentage),
        completed_at=test.completed_at.isoformat(),
    )
