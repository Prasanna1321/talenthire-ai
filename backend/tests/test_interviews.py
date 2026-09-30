"""
tests/test_interviews.py
----------------------------
Tests for AI Question Generator, Mock Interview, Answer Evaluation, AI
Feedback, and Interview Reports modules. Belongs in: backend/tests/test_interviews.py

Gemini (question/feedback generation) and the sentence-transformer answer
evaluator are mocked so tests run deterministically without needing a
live GEMINI_API_KEY or GPU-backed embedding model.
"""

from unittest.mock import patch

from app.models.interview import InterviewQuestion, Score, Feedback


def _fake_generate_questions(db, job_id, job_role, skills, num_questions, difficulty):
    questions = []
    for i in range(num_questions):
        q = InterviewQuestion(
            job_id=job_id,
            question_text=f"Sample question {i+1} about {job_role}",
            question_type="technical",
            difficulty="medium",
            ideal_answer="A strong, specific reference answer covering the key concept.",
            generated_by="gemini",
        )
        db.add(q)
        questions.append(q)
    db.commit()
    for q in questions:
        db.refresh(q)
    return questions


def _fake_evaluate_answer(db, answer, question):
    score = Score(
        answer_id=answer.answer_id,
        similarity_score=0.82,
        relevance_score=82.0,
        fluency_score=75.0,
        confidence_score=90.0,
        final_score=81.5,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def _fake_generate_feedback(db, session, visual_metrics=None):
    feedback = Feedback(
        session_id=session.session_id,
        strengths="Clear articulation of core ML concepts.",
        areas_to_improve="Provide more concrete examples from past projects.",
        detailed_feedback="Overall a solid mock interview performance with room to grow on specificity.",
        overall_rating=7.5,
        generated_by="gemini",
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


JOB_PAYLOAD = {
    "title": "Gen AI Engineer Intern",
    "description": "Work on LLM-based products.",
    "required_skills": ["Python", "LLM"],
    "experience_level": "entry",
    "location": "Bengaluru",
    "job_type": "internship",
}


@patch("app.routers.interviews.generate_and_store_questions", side_effect=_fake_generate_questions)
def test_recruiter_can_generate_questions(mock_gen, client, recruiter_token):
    job_res = client.post("/api/jobs", json=JOB_PAYLOAD, headers=recruiter_token)
    job_id = job_res.json()["job_id"]

    response = client.post(
        "/api/interviews/questions/generate",
        json={"job_id": job_id, "num_questions": 3, "difficulty": "mixed"},
        headers=recruiter_token,
    )
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_candidate_can_start_session(client, candidate_token, completed_aptitude_test):
    response = client.post(
        "/api/interviews/sessions/start",
        json={"session_type": "mock"},
        headers=candidate_token,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "in_progress"


@patch("app.routers.interviews.generate_and_store_questions", side_effect=_fake_generate_questions)
@patch("app.routers.interviews.evaluate_answer", side_effect=_fake_evaluate_answer)
def test_full_mock_interview_flow(mock_eval, mock_gen, client, recruiter_token, candidate_token, completed_aptitude_test):
    # Recruiter posts a job and generates questions
    job_res = client.post("/api/jobs", json=JOB_PAYLOAD, headers=recruiter_token)
    job_id = job_res.json()["job_id"]
    q_res = client.post(
        "/api/interviews/questions/generate",
        json={"job_id": job_id, "num_questions": 1},
        headers=recruiter_token,
    )
    question_id = q_res.json()[0]["question_id"]

    # Candidate starts a session and submits a typed answer
    session_res = client.post(
        "/api/interviews/sessions/start", json={"job_id": job_id, "session_type": "mock"}, headers=candidate_token
    )
    session_id = session_res.json()["session_id"]

    answer_res = client.post(
        f"/api/interviews/sessions/{session_id}/answer/text",
        json={"session_id": session_id, "question_id": question_id, "transcribed_text": "My detailed answer."},
        headers=candidate_token,
    )
    assert answer_res.status_code == 200
    assert answer_res.json()["final_score"] == 81.5


@patch("app.routers.interviews.generate_session_feedback", side_effect=_fake_generate_feedback)
def test_complete_session_generates_feedback(mock_feedback, client, candidate_token, completed_aptitude_test):
    session_res = client.post(
        "/api/interviews/sessions/start", json={"session_type": "mock"}, headers=candidate_token
    )
    session_id = session_res.json()["session_id"]

    response = client.post(f"/api/interviews/sessions/{session_id}/complete", headers=candidate_token)
    assert response.status_code == 200
    assert response.json()["overall_rating"] == 7.5


def test_candidate_cannot_access_others_session(client, candidate_token, completed_aptitude_test):
    # A session ID that doesn't belong to this candidate (or doesn't exist)
    response = client.post("/api/interviews/sessions/99999/complete", headers=candidate_token)
    assert response.status_code == 404
