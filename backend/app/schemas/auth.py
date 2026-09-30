"""
app/schemas/auth.py
--------------------
Pydantic request/response models for registration, login, and JWT tokens.
Belongs in: backend/app/schemas/auth.py
"""

from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Literal["candidate", "recruiter", "admin"]

    # Optional profile fields depending on role
    company_name: Optional[str] = None       # required if role == recruiter
    phone: Optional[str] = None              # candidate
    location: Optional[str] = None           # candidate


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# PHASE 2: OTP verification + forgot/reset password
# ---------------------------------------------------------------------------
class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: Literal["email_verification", "password_reset"]


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    purpose: Literal["email_verification", "password_reset"]


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    detail: str
