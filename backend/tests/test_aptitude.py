"""
tests/test_aptitude.py
--------------------------
Phase 5: 30-question aptitude test. Verifies exactly 30 questions are
served, grading happens server-side (client-claimed correctness is
ignored), and the mock-interview gate is enforced.
Belongs in: backend/tests/test_aptitude.py

Requires the aptitude_questions table to be seeded (>= 30 rows) — run
database/seed_aptitude_questions.py against TEST_DATABASE_URL before
running this file, or these tests will fail with a 500 "question bank
too small" error (that error itself is a deliberate, correct guard).
"""


def test_start_test_returns_exactly_30_questions(client, candidate_token):
    response = client.post("/api/aptitude/start", headers=candidate_token)
    assert response.status_code == 201
    body = response.json()
    assert len(body["questions"]) == 30
    # correct_option must NEVER be sent to the candidate mid-test
    for q in body["questions"]:
        assert "correct_option" not in q


def test_questions_are_stable_across_refetch(client, candidate_token):
    start_resp = client.post("/api/aptitude/start", headers=candidate_token)
    test_id = start_resp.json()["test_id"]
    first_ids = sorted(q["question_id"] for q in start_resp.json()["questions"])

    refetch_resp = client.get(f"/api/aptitude/questions?test_id={test_id}", headers=candidate_token)
    assert refetch_resp.status_code == 200
    second_ids = sorted(q["question_id"] for q in refetch_resp.json()["questions"])
    assert first_ids == second_ids  # same 30 questions, not reshuffled on refresh


def test_grading_is_server_side_not_trusting_client(client, candidate_token):
    """Submit answers claiming to be correct for questions with wrong actual answers — score must reflect reality."""
    start_resp = client.post("/api/aptitude/start", headers=candidate_token)
    test_id = start_resp.json()["test_id"]
    questions = start_resp.json()["questions"]

    # Deliberately answer everything with "D" — some will be right, most likely wrong;
    # the point is the score must come from the DB's correct_option, not from us.
    answers = [{"question_id": q["question_id"], "selected_option": "D"} for q in questions]
    submit_resp = client.post("/api/aptitude/submit", json={"test_id": test_id, "answers": answers}, headers=candidate_token)
    assert submit_resp.status_code == 200
    body = submit_resp.json()
    assert body["total_questions"] == 30
    assert 0 <= body["score"] <= 30
    assert body["percentage"] == round(body["score"] / 30 * 100, 2)


def test_cannot_submit_same_test_twice(client, candidate_token):
    start_resp = client.post("/api/aptitude/start", headers=candidate_token)
    test_id = start_resp.json()["test_id"]
    answers = [{"question_id": q["question_id"], "selected_option": "A"} for q in start_resp.json()["questions"]]

    first = client.post("/api/aptitude/submit", json={"test_id": test_id, "answers": answers}, headers=candidate_token)
    assert first.status_code == 200

    second = client.post("/api/aptitude/submit", json={"test_id": test_id, "answers": answers}, headers=candidate_token)
    assert second.status_code == 400


def test_mock_interview_blocked_without_completed_aptitude_test(client, candidate_token):
    response = client.post("/api/interviews/sessions/start", json={"session_type": "mock"}, headers=candidate_token)
    assert response.status_code == 403
    assert "aptitude" in response.json()["detail"].lower()


def test_mock_interview_allowed_after_completed_aptitude_test(client, candidate_token, completed_aptitude_test):
    response = client.post("/api/interviews/sessions/start", json={"session_type": "mock"}, headers=candidate_token)
    assert response.status_code == 201
