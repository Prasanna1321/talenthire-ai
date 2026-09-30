"""
app/services/otp_service.py
-------------------------------
Phase 2: OTP generation, hashing, verification, and rate/attempt limiting.
Belongs in: backend/app/services/otp_service.py

Security notes:
- OTPs are 6-digit, generated with `secrets` (cryptographically secure),
  never sequential/predictable.
- Only the bcrypt HASH of the OTP is stored — never the plaintext code.
- Each OTP has a short expiry (10 minutes) and a max wrong-guess count
  (5 attempts) before it's permanently invalidated.
"""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password  # bcrypt helpers, reused for OTP hashing
from app.models.otp import EmailOTP
from app.models.user import User

OTP_EXPIRY_MINUTES = 10
OTP_LENGTH = 6


def _generate_numeric_otp(length: int = OTP_LENGTH) -> str:
    """Cryptographically secure random numeric OTP, e.g. '482913'."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def create_otp(db: Session, user: User, purpose: str) -> str:
    """
    Generates a new OTP, invalidates any previous unused OTP of the same
    purpose for this user, stores only its hash, and returns the plaintext
    code (the ONLY time it exists in plaintext) so the caller can email it.
    """
    db.query(EmailOTP).filter(
        EmailOTP.user_id == user.user_id,
        EmailOTP.purpose == purpose,
        EmailOTP.used.is_(False),
    ).update({"used": True})

    code = _generate_numeric_otp()
    otp_row = EmailOTP(
        user_id=user.user_id,
        otp_hash=hash_password(code),  # reuse the bcrypt helper — OTPs are short but bcrypt handles that fine
        purpose=purpose,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    db.add(otp_row)
    db.commit()
    return code


class OTPVerificationError(Exception):
    """Raised with a human-readable reason when OTP verification fails."""


def verify_otp(db: Session, user: User, code: str, purpose: str) -> None:
    """
    Verifies a submitted OTP. Raises OTPVerificationError with a specific
    message on any failure; returns normally (None) only on success.
    Marks the OTP as used on success so it cannot be replayed.
    """
    otp_row = (
        db.query(EmailOTP)
        .filter(EmailOTP.user_id == user.user_id, EmailOTP.purpose == purpose, EmailOTP.used.is_(False))
        .order_by(EmailOTP.created_at.desc())
        .first()
    )
    if not otp_row:
        raise OTPVerificationError("No active OTP found. Please request a new one.")

    if datetime.now(timezone.utc) > otp_row.expires_at.replace(tzinfo=timezone.utc):
        otp_row.used = True
        db.commit()
        raise OTPVerificationError("This OTP has expired. Please request a new one.")

    if otp_row.attempts >= otp_row.max_attempts:
        otp_row.used = True
        db.commit()
        raise OTPVerificationError("Too many incorrect attempts. Please request a new OTP.")

    if not verify_password(code, otp_row.otp_hash):
        otp_row.attempts += 1
        db.commit()
        remaining = otp_row.max_attempts - otp_row.attempts
        raise OTPVerificationError(f"Incorrect OTP. {remaining} attempt(s) remaining.")

    otp_row.used = True
    db.commit()
