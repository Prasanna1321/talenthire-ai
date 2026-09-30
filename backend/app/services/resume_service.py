"""
app/services/resume_service.py
--------------------------------
Resume processing pipeline for TalentHire AI.

Includes:
- Resume upload
- Resume parsing
- Resume classification
- Candidate identity verification
- Identity consistency checking
- ATS scoring
- Resume versioning

Important:
A candidate cannot upload another person's resume.
The uploaded resume is checked against the logged-in
candidate's registered profile BEFORE ATS scoring.
"""

import os
import sys
import uuid
import re
from typing import List, Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.profile import Candidate
from app.models.resume import Resume
from app.services.ats_service import compute_ats_score
from app.services.consistency_service import (
    extract_identity,
    check_consistency,
    ExtractedIdentity,
)


ML_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml")
)

if ML_DIR not in sys.path:
    sys.path.append(ML_DIR)


# ============================================================
# ML LOADERS
# ============================================================

def _get_resume_parser():
    """Lazy-load resume parser."""
    from resume_parser.parser import get_resume_parser
    return get_resume_parser()


def _get_resume_classifier():
    """Lazy-load resume classifier."""
    from resume_classifier.classify import get_resume_classifier
    return get_resume_classifier()


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def _normalize_name(value: Optional[str]) -> str:
    """
    Normalize names for comparison.

    Example:
        "Poornima K" -> "poornima k"
        "POORNIMA   K" -> "poornima k"
    """

    if not value:
        return ""

    value = value.lower().strip()

    # Remove punctuation
    value = re.sub(r"[^a-zA-Z\s]", " ", value)

    # Normalize spaces
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _normalize_email(value: Optional[str]) -> str:
    """Normalize email address."""

    if not value:
        return ""

    return value.strip().lower()


def _normalize_phone(value: Optional[str]) -> str:
    """
    Normalize phone number.

    Keeps only digits.

    Example:
        +91 98765 43210 -> 919876543210
    """

    if not value:
        return ""

    return re.sub(r"\D", "", value)


# ============================================================
# NAME MATCHING
# ============================================================

def _name_matches(
    registered_name: Optional[str],
    resume_name: Optional[str],
) -> bool:
    """
    Compare registered candidate name with resume name.

    We intentionally use a flexible comparison because names
    may appear in different formats.

    Examples:

        Poornima K
        POORNIMA K
        Poornima Kumar

    can be considered a match when the meaningful name parts
    overlap.

    Completely different names such as:

        Poornima K
        Prasanna Kumar

    will fail.
    """

    registered = _normalize_name(registered_name)
    resume = _normalize_name(resume_name)

    if not registered or not resume:
        return False

    registered_words = set(registered.split())
    resume_words = set(resume.split())

    # Exact normalized match
    if registered == resume:
        return True

    # Require the first name to match.
    registered_first = registered.split()[0]
    resume_first = resume.split()[0]

    if registered_first != resume_first:
        return False

    # If first names match, accept.
    # This handles middle/last-name variations.
    return True


# ============================================================
# CANDIDATE IDENTITY VERIFICATION
# ============================================================

def verify_resume_belongs_to_candidate(
    db: Session,
    candidate_id: int,
    identity: ExtractedIdentity,
) -> Optional[str]:
    """
    Verify that the uploaded resume belongs to the logged-in
    candidate.

    Returns:
        None -> identity appears valid
        str  -> human-readable rejection message

    This check happens BEFORE ATS scoring.
    """

    # --------------------------------------------------------
    # Load candidate profile
    # --------------------------------------------------------

    candidate = (
        db.query(Candidate)
        .filter(Candidate.candidate_id == candidate_id)
        .first()
    )

    if not candidate:
        return "Candidate profile not found."

    # --------------------------------------------------------
    # Load user account
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.user_id == candidate.user_id)
        .first()
    )

    if not user:
        return "Candidate account not found."

    registered_name = user.full_name
    registered_email = user.email
    registered_phone = candidate.phone

    # --------------------------------------------------------
    # Make sure the resume contains identity information
    # --------------------------------------------------------

    if not identity.name and not identity.email and not identity.phone:
        return (
            "We could not identify the candidate from the uploaded resume. "
            "Please upload a resume containing your name and contact details."
        )

    # --------------------------------------------------------
    # EMAIL CHECK
    #
    # If both registered email and resume email exist,
    # they must match.
    # --------------------------------------------------------

    if registered_email and identity.email:

        registered_email_normalized = _normalize_email(
            registered_email
        )

        resume_email_normalized = _normalize_email(
            identity.email
        )

        if registered_email_normalized != resume_email_normalized:

            return (
                "Resume verification failed. "
                "The email address in the uploaded resume does not "
                "match the email address of the logged-in candidate."
            )

    # --------------------------------------------------------
    # PHONE CHECK
    #
    # Only compare when BOTH values exist.
    # --------------------------------------------------------

    if registered_phone and identity.phone:

        registered_phone_normalized = _normalize_phone(
            registered_phone
        )

        resume_phone_normalized = _normalize_phone(
            identity.phone
        )

        # Compare last 10 digits to handle +91 formatting.
        registered_last10 = registered_phone_normalized[-10:]
        resume_last10 = resume_phone_normalized[-10:]

        if (
            registered_last10
            and resume_last10
            and registered_last10 != resume_last10
        ):

            return (
                "Resume verification failed. "
                "The phone number in the uploaded resume does not "
                "match the logged-in candidate."
            )

    # --------------------------------------------------------
    # NAME CHECK
    # --------------------------------------------------------

    if registered_name and identity.name:

        if not _name_matches(
            registered_name,
            identity.name,
        ):

            return (
                "Resume verification failed. "
                f"The uploaded resume appears to belong to "
                f"'{identity.name}', but the logged-in candidate "
                f"is '{registered_name}'. "
                "Please upload your own resume."
            )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    return None


# ============================================================
# FILE STORAGE
# ============================================================

def save_uploaded_file(
    upload: UploadFile,
    candidate_id: int,
) -> str:

    os.makedirs(
        settings.RESUME_UPLOAD_DIR,
        exist_ok=True,
    )

    ext = os.path.splitext(
        upload.filename or ""
    )[1] or ".pdf"

    unique_name = (
        f"candidate_{candidate_id}_"
        f"{uuid.uuid4().hex}"
        f"{ext}"
    )

    dest_path = os.path.join(
        settings.RESUME_UPLOAD_DIR,
        unique_name,
    )

    with open(dest_path, "wb") as f:
        f.write(upload.file.read())

    return dest_path


# ============================================================
# MAIN RESUME PROCESSING
# ============================================================

def process_resume(
    db: Session,
    candidate_id: int,
    upload: UploadFile,
    force: bool = False,
) -> dict:

    """
    Full resume processing pipeline.

    Pipeline:

        Upload
          ↓
        Parse
          ↓
        Extract identity
          ↓
        Verify against logged-in candidate
          ↓
        Existing-resume consistency check
          ↓
        ATS scoring
          ↓
        Save version

    IMPORTANT:
    The candidate identity check cannot be bypassed with force=True.

    force is retained only for compatibility with the existing
    API and existing-resume version consistency behaviour.
    """

    # ========================================================
    # 1. Save uploaded file
    # ========================================================

    file_path = save_uploaded_file(
        upload,
        candidate_id,
    )

    # ========================================================
    # 2. Parse resume
    # ========================================================

    parser = _get_resume_parser()

    parsed = parser.parse(
        file_path
    )

    # ========================================================
    # 3. Extract candidate identity
    # ========================================================

    identity = extract_identity(
        parsed.raw_text
    )

    # ========================================================
    # 4. VERIFY AGAINST LOGGED-IN CANDIDATE
    #
    # This happens BEFORE ATS scoring.
    # ========================================================

    identity_error = verify_resume_belongs_to_candidate(
        db,
        candidate_id,
        identity,
    )

    if identity_error:

        # Delete the uploaded file because it was rejected.
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass

        raise HTTPException(
            status_code=422,
            detail=identity_error,
        )

    # ========================================================
    # 5. Resume classification
    # ========================================================

    classifier = _get_resume_classifier()

    classification = classifier.predict(
        parsed.cleaned_text
    )

    # ========================================================
    # 6. Check consistency with existing current resume
    #
    # This is an additional protection.
    # ========================================================

    existing_current = (
        db.query(Resume)
        .filter(
            Resume.candidate_id == candidate_id,
            Resume.is_current.is_(True),
        )
        .order_by(
            Resume.version_number.desc()
        )
        .first()
    )

    if existing_current and not force:

        existing_identity = ExtractedIdentity(
            name=existing_current.extracted_name,
            email=existing_current.extracted_email,
            phone=existing_current.extracted_phone,
        )

        warning = check_consistency(
            identity,
            existing_identity,
        )

        if warning:

            # Delete the new file because it has not been accepted.
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass

            return {
                "requires_confirmation": True,
                "warning": warning,
            }

    # ========================================================
    # 7. ATS SCORE
    #
    # Only reached after candidate verification.
    # ========================================================

    ats_result = compute_ats_score(
        parsed.raw_text,
        parsed.extracted_skills,
        job_required_skills=None,
        email=identity.email,
        phone=identity.phone,
    )

    # ========================================================
    # 8. Create new resume version
    # ========================================================

    new_version = 1

    if existing_current:

        existing_current.is_current = False

        new_version = (
            existing_current.version_number + 1
        )

    # ========================================================
    # 9. Create database record
    # ========================================================

    resume = Resume(
        candidate_id=candidate_id,
        file_path=file_path,
        original_filename=upload.filename,
        raw_text=parsed.raw_text,
        extracted_skills=parsed.extracted_skills,
        predicted_category=classification.predicted_category,
        prediction_confidence=classification.confidence,
        embedding=parsed.embedding,
        version_number=new_version,
        is_current=True,
        extracted_name=identity.name,
        extracted_email=identity.email,
        extracted_phone=identity.phone,
        ats_score=ats_result.total_score,
        ats_breakdown=ats_result.breakdown,
    )

    # ========================================================
    # 10. Save
    # ========================================================

    db.add(resume)

    db.commit()

    db.refresh(resume)

    return {
        "requires_confirmation": False,
        "resume": resume,
    }


# ============================================================
# JOB SKILL MATCH
# ============================================================

def compute_skill_match_score(
    resume_skills: List[str],
    job_skills: List[str],
) -> float:

    """Simple, explainable job-match score."""

    if not job_skills:
        return 0.0

    resume_set = {
        s.lower()
        for s in resume_skills or []
    }

    job_set = {
        s.lower()
        for s in job_skills
    }

    overlap = resume_set.intersection(
        job_set
    )

    return round(
        len(overlap) / len(job_set) * 100,
        2,
    )