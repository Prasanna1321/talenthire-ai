"""
tests/test_auth.py
--------------------
Tests for the User Authentication Module: register, OTP email verification,
login, forgot/reset password, JWT. Belongs in: backend/tests/test_auth.py
"""

from app.models.user import User
from app.services.otp_service import create_otp


def test_register_candidate_returns_pending_verification(client):
    response = client.post("/api/auth/register", json={
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "password": "SecurePass123!",
        "role": "candidate",
    })
    assert response.status_code == 201
    body = response.json()
    # PHASE 2: registration no longer issues tokens directly — email must be verified first
    assert "verification code" in body["detail"].lower()
    assert "access_token" not in body


def test_register_recruiter_requires_company_name(client):
    response = client.post("/api/auth/register", json={
        "full_name": "Recruiter Bob",
        "email": "bob@example.com",
        "password": "SecurePass123!",
        "role": "recruiter",
        # company_name intentionally omitted
    })
    assert response.status_code == 400


def test_register_duplicate_email_rejected(client):
    payload = {
        "full_name": "Dup User",
        "email": "dup@example.com",
        "password": "SecurePass123!",
        "role": "candidate",
    }
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 400


def test_login_blocked_before_email_verification(client):
    client.post("/api/auth/register", json={
        "full_name": "Unverified User",
        "email": "unverified@example.com",
        "password": "SecurePass123!",
        "role": "candidate",
    })
    response = client.post("/api/auth/login", json={"email": "unverified@example.com", "password": "SecurePass123!"})
    assert response.status_code == 403
    assert "verify" in response.json()["detail"].lower()


def test_verify_otp_then_login_succeeds(client, db_session):
    client.post("/api/auth/register", json={
        "full_name": "Login User",
        "email": "login@example.com",
        "password": "SecurePass123!",
        "role": "candidate",
    })
    user = db_session.query(User).filter(User.email == "login@example.com").first()
    otp_code = create_otp(db_session, user, purpose="email_verification")

    verify_resp = client.post("/api/auth/verify-otp", json={
        "email": "login@example.com", "otp": otp_code, "purpose": "email_verification",
    })
    assert verify_resp.status_code == 200
    assert "access_token" in verify_resp.json()

    login_resp = client.post("/api/auth/login", json={"email": "login@example.com", "password": "SecurePass123!"})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_verify_otp_wrong_code_rejected(client, db_session):
    client.post("/api/auth/register", json={
        "full_name": "Wrong OTP User",
        "email": "wrongotp@example.com",
        "password": "SecurePass123!",
        "role": "candidate",
    })
    user = db_session.query(User).filter(User.email == "wrongotp@example.com").first()
    create_otp(db_session, user, purpose="email_verification")  # real code generated but we submit a wrong one

    response = client.post("/api/auth/verify-otp", json={
        "email": "wrongotp@example.com", "otp": "000000", "purpose": "email_verification",
    })
    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"].lower()


def test_login_wrong_password_rejected(client, db_session):
    client.post("/api/auth/register", json={
        "full_name": "Login User 2",
        "email": "login2@example.com",
        "password": "SecurePass123!",
        "role": "candidate",
    })
    user = db_session.query(User).filter(User.email == "login2@example.com").first()
    otp_code = create_otp(db_session, user, purpose="email_verification")
    client.post("/api/auth/verify-otp", json={"email": "login2@example.com", "otp": otp_code, "purpose": "email_verification"})

    response = client.post("/api/auth/login", json={"email": "login2@example.com", "password": "WrongPass!"})
    assert response.status_code == 401


def test_forgot_password_reset_flow(client, db_session):
    client.post("/api/auth/register", json={
        "full_name": "Reset User",
        "email": "reset@example.com",
        "password": "OldPass123!",
        "role": "candidate",
    })
    user = db_session.query(User).filter(User.email == "reset@example.com").first()
    verify_code = create_otp(db_session, user, purpose="email_verification")
    client.post("/api/auth/verify-otp", json={"email": "reset@example.com", "otp": verify_code, "purpose": "email_verification"})

    # Forgot password: generate a real reset OTP directly (standing in for the emailed one)
    reset_code = create_otp(db_session, user, purpose="password_reset")
    reset_resp = client.post("/api/auth/reset-password", json={
        "email": "reset@example.com", "otp": reset_code, "new_password": "NewPass456!",
    })
    assert reset_resp.status_code == 200

    old_login = client.post("/api/auth/login", json={"email": "reset@example.com", "password": "OldPass123!"})
    assert old_login.status_code == 401

    new_login = client.post("/api/auth/login", json={"email": "reset@example.com", "password": "NewPass456!"})
    assert new_login.status_code == 200


def test_protected_endpoint_requires_token(client):
    response = client.get("/api/users/me")
    assert response.status_code == 401


def test_protected_endpoint_with_valid_token(client, candidate_token):
    response = client.get("/api/users/me", headers=candidate_token)
    assert response.status_code == 200
    assert response.json()["role"] == "candidate"
