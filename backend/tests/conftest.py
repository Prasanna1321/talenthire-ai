"""
tests/conftest.py
--------------------
Shared pytest fixtures for the backend test suite.
Belongs in: backend/tests/conftest.py

IMPORTANT: Tests run against a real PostgreSQL database (NOT SQLite),
because several models use PostgreSQL's native ARRAY/JSONB column types.
Point TEST_DATABASE_URL at a disposable local/test database before running:

    export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/talenthire_test_db
    pytest

Each test function runs inside its own transaction that is rolled back at
the end, so tests never leave residue in the test database.

PHASE 2/3 NOTE: registration no longer returns tokens directly — it sends
an OTP and requires /verify-otp before login works. The candidate_token/
recruiter_token fixtures below call create_otp() directly (bypassing real
email delivery, which needs RESEND_API_KEY) to get a valid code, then call
/verify-otp for real, exactly like the real flow would after the candidate
reads their email. recruiter_token also simulates admin approval (Phase 3)
so existing job-management tests reflect an APPROVED recruiter, matching
how the app is actually used; a separate pending_recruiter_token fixture
covers the "not yet approved" case explicitly.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://postgres:Pk%401321@localhost:5432/talenthire_test_db"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.profile import Recruiter  # noqa: E402
from app.services.otp_service import create_otp  # noqa: E402

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Creates all tables once before the test session, seeds the aptitude
    question bank (needed for Phase 5 tests), and drops everything after."""
    Base.metadata.create_all(bind=engine)

    import sys as _sys
    import os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "..", "database"))
    from seed_aptitude_questions import QUESTIONS  # noqa: E402

    with engine.begin() as conn:
        from sqlalchemy import text as _text
        for category, question_text, a, b, c, d, correct in QUESTIONS:
            conn.execute(
                _text("""
                    INSERT INTO aptitude_questions
                        (category, question_text, option_a, option_b, option_c, option_d, correct_option)
                    VALUES (:category, :question_text, :a, :b, :c, :d, :correct)
                """),
                {"category": category, "question_text": question_text, "a": a, "b": b, "c": c, "d": d, "correct": correct},
            )

    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Yields a SQLAlchemy session wrapped in a transaction that's rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with the DB dependency overridden to use the rolled-back test session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _register_and_verify(client, db_session, payload) -> dict:
    """Registers a user, verifies their email via a directly-generated OTP
    (standing in for the real emailed code), and returns the login token response."""
    register_resp = client.post("/api/auth/register", json=payload)
    assert register_resp.status_code == 201, register_resp.text

    user = db_session.query(User).filter(User.email == payload["email"]).first()
    otp_code = create_otp(db_session, user, purpose="email_verification")

    verify_resp = client.post("/api/auth/verify-otp", json={
        "email": payload["email"], "otp": otp_code, "purpose": "email_verification",
    })
    assert verify_resp.status_code == 200, verify_resp.text
    return verify_resp.json()


@pytest.fixture()
def candidate_token(client, db_session):
    """Registers + verifies a candidate and returns their auth headers."""
    tokens = _register_and_verify(client, db_session, {
        "full_name": "Test Candidate",
        "email": "candidate@test.com",
        "password": "TestPass123!",
        "role": "candidate",
        "phone": "1234567890",
        "location": "Shivamogga",
    })
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def pending_recruiter_token(client, db_session):
    """Registers + verifies a recruiter WITHOUT approving them (Phase 3 pending state)."""
    tokens = _register_and_verify(client, db_session, {
        "full_name": "Pending Recruiter",
        "email": "pending.recruiter@test.com",
        "password": "TestPass123!",
        "role": "recruiter",
        "company_name": "PendingCorp",
    })
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def recruiter_token(client, db_session):
    """Registers + verifies a recruiter AND simulates admin approval (Phase 3),
    so existing job-management tests exercise an approved recruiter."""
    tokens = _register_and_verify(client, db_session, {
        "full_name": "Test Recruiter",
        "email": "recruiter@test.com",
        "password": "TestPass123!",
        "role": "recruiter",
        "company_name": "TestCorp",
    })
    recruiter = db_session.query(Recruiter).filter(Recruiter.user_id == tokens["user_id"]).first()
    recruiter.status = "approved"
    db_session.commit()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def admin_token(client, db_session):
    """Registers + verifies an admin and returns their auth headers."""
    tokens = _register_and_verify(client, db_session, {
        "full_name": "Test Admin",
        "email": "admin@test.com",
        "password": "TestPass123!",
        "role": "admin",
    })
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def completed_aptitude_test(client, candidate_token):
    """
    Starts and submits a full aptitude test for the candidate_token fixture's
    user, satisfying the Phase 5 gate before a mock interview can start.
    Other fixtures/tests that need `candidate_token` AND an interview session
    should also depend on this fixture.
    """
    start_resp = client.post("/api/aptitude/start", headers=candidate_token)
    assert start_resp.status_code == 201, start_resp.text
    data = start_resp.json()
    answers = [{"question_id": q["question_id"], "selected_option": "A"} for q in data["questions"]]
    submit_resp = client.post("/api/aptitude/submit", json={"test_id": data["test_id"], "answers": answers}, headers=candidate_token)
    assert submit_resp.status_code == 200, submit_resp.text
    return submit_resp.json()
