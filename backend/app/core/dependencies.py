"""
app/core/dependencies.py
-------------------------
FastAPI dependencies for authentication and role-based authorization.
Belongs in: backend/app/core/dependencies.py

Usage in a router:
    @router.get("/candidate/dashboard")
    def dashboard(user: User = Depends(require_role("candidate"))):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User
from app.models.profile import Recruiter

# Points Swagger UI's "Authorize" button at the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Decodes the bearer token, loads the corresponding user from the DB,
    and rejects the request with 401 if anything is invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*allowed_roles: str):
    """
    Dependency factory that restricts an endpoint to one or more roles.
    e.g. Depends(require_role("recruiter", "admin"))
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


def require_approved_recruiter(db: Session = Depends(get_db), current_user: User = Depends(require_role("recruiter"))) -> User:
    """
    PHASE 3: Backend enforcement of recruiter approval status. This is the
    actual security boundary — the frontend hiding "Post Job" buttons for
    pending recruiters is a UX nicety, not a security control. Use this
    dependency (instead of plain require_role("recruiter")) on every
    job-management endpoint: create/update/delete job.
    """
    recruiter = db.query(Recruiter).filter(Recruiter.user_id == current_user.user_id).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")
    if recruiter.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your recruiter account is '{recruiter.status}'. Job management requires admin approval.",
        )
    return current_user
