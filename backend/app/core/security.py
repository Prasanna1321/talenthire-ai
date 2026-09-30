"""
app/core/security.py
---------------------
Password hashing (bcrypt via passlib) and JWT access/refresh token
creation + verification. Belongs in: backend/app/core/security.py
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt, JWTError

from app.config import settings

# NOTE: password hashing uses the `bcrypt` library directly rather than
# passlib's CryptContext. passlib (last released 2020) relies on an
# internal `bcrypt.__about__.__version__` attribute that was removed in
# bcrypt>=4.1, which breaks passlib's startup self-test with a
# "password cannot be longer than 72 bytes" error even for short,
# perfectly valid passwords. Calling bcrypt directly avoids that
# unmaintained-dependency trap entirely.

_BCRYPT_MAX_BYTES = 72  # bcrypt's hard input-length limit


def _truncate_to_bcrypt_limit(password: str) -> bytes:
    """
    bcrypt silently ignores/rejects input beyond 72 bytes. Truncating on
    the UTF-8 byte boundary (not the character boundary) keeps this safe
    for multi-byte characters while matching bcrypt's own limit.
    """
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    """Hash a plaintext password before storing it in users.password_hash."""
    hashed = bcrypt.hashpw(_truncate_to_bcrypt_limit(plain_password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a login attempt's password against the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(_truncate_to_bcrypt_limit(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a short-lived JWT access token.
    `data` typically contains {"sub": user_id, "role": role}.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a longer-lived JWT refresh token used to mint new access tokens."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT. Raises jose.JWTError if invalid/expired —
    callers (see core/dependencies.py) turn that into a 401 response.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
