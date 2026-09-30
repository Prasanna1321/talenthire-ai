"""
app/routers/auth.py
--------------------
User Authentication Module + Phase 2 OTP verification / password reset.
Belongs in: backend/app/routers/auth.py

Endpoints:
    POST /api/auth/register        -> creates user (unverified), emails OTP
    POST /api/auth/login           -> blocked until email_verified=True
    POST /api/auth/refresh
    POST /api/auth/send-otp        -> (re)send an OTP for a given purpose
    POST /api/auth/verify-otp      -> verify email OR authorize a password reset
    POST /api/auth/forgot-password -> sends a password-reset OTP
    POST /api/auth/reset-password  -> consumes OTP, sets new password
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.database import get_db
from app.models.user import User
from app.models.profile import Candidate, Recruiter
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest,
    SendOTPRequest, VerifyOTPRequest, ForgotPasswordRequest, ResetPasswordRequest,
    MessageResponse,
)
from app.services.otp_service import create_otp, verify_otp, OTPVerificationError
from app.services.email_service import send_otp_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Creates the user as UNVERIFIED and emails a 6-digit OTP. No access token
    is issued here — the frontend must call /verify-otp before /login will
    succeed. This is the enforcement point for "no login before email
    verification", not just a frontend redirect.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.role == "recruiter" and not payload.company_name:
        raise HTTPException(status_code=400, detail="company_name is required for recruiter registration")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        email_verified=False,
    )
    db.add(user)
    db.flush()  # get user.user_id before commit, needed for the profile FK

    if payload.role == "candidate":
        db.add(Candidate(user_id=user.user_id, phone=payload.phone, location=payload.location))
    elif payload.role == "recruiter":
        db.add(Recruiter(user_id=user.user_id, company_name=payload.company_name, status="pending"))
    # 'admin' role has no extra profile table

    db.commit()
    db.refresh(user)

    otp_code = create_otp(db, user, purpose="email_verification")
    send_otp_email(user.email, user.full_name, otp_code, purpose="email_verification")

    return MessageResponse(detail="Registration successful. A verification code has been sent to your email.")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")

    return _build_token_response(user)


@router.post("/login/form", response_model=TokenResponse, include_in_schema=False)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2-compatible form login so Swagger UI's 'Authorize' button works directly."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")
    return _build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.user_id == int(decoded["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")

    return _build_token_response(user)


# ---------------------------------------------------------------------------
# PHASE 2: OTP verification + forgot/reset password
# ---------------------------------------------------------------------------
@router.post("/send-otp", response_model=MessageResponse)
def send_otp(payload: SendOTPRequest, db: Session = Depends(get_db)):
    """Resend/issue an OTP for email verification or password reset."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Don't reveal whether an email is registered — respond the same either way
        return MessageResponse(detail="If that email is registered, a verification code has been sent.")

    otp_code = create_otp(db, user, purpose=payload.purpose)
    send_otp_email(user.email, user.full_name, otp_code, purpose=payload.purpose)
    return MessageResponse(detail="If that email is registered, a verification code has been sent.")


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp_endpoint(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verifies an email_verification OTP, marks the account verified, and logs
    the user in immediately (returns tokens) so registration feels seamless.
    (For purpose=password_reset, use /reset-password instead — that endpoint
    verifies the OTP itself as part of setting the new password.)
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found for this email")

    try:
        verify_otp(db, user, payload.otp, purpose=payload.purpose)
    except OTPVerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if payload.purpose == "email_verification":
        user.email_verified = True
        db.commit()
        db.refresh(user)

    return _build_token_response(user)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        otp_code = create_otp(db, user, purpose="password_reset")
        send_otp_email(user.email, user.full_name, otp_code, purpose="password_reset")
    # Same response whether or not the email exists, to avoid leaking account existence
    return MessageResponse(detail="If that email is registered, a password reset code has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found for this email")

    try:
        verify_otp(db, user, payload.otp, purpose="password_reset")
    except OTPVerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return MessageResponse(detail="Password reset successful. Please log in with your new password.")


def _build_token_response(user: User) -> TokenResponse:
    token_data = {"sub": str(user.user_id), "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        role=user.role,
        user_id=user.user_id,
        full_name=user.full_name,
    )
