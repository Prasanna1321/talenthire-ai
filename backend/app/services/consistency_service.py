"""
app/services/consistency_service.py
---------------------------------------
Phase 4: extract candidate identity (name/email/phone) from resume text and
compare against the candidate's existing current resume, so a new upload
that looks like it belongs to a different person triggers a warning instead
of silently replacing the old one. Belongs in: backend/app/services/consistency_service.py

Uses simple regex for email/phone (reliable, no ML needed) and a light
heuristic for "name" (first non-empty line that looks like a name, since
resumes overwhelmingly put the candidate's name at the very top).
"""

import re
from dataclasses import dataclass
from typing import Optional

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")


@dataclass
class ExtractedIdentity:
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]


def extract_identity(raw_text: str) -> ExtractedIdentity:
    email_match = EMAIL_RE.search(raw_text)
    phone_match = PHONE_RE.search(raw_text)

    name = None
    for line in raw_text.strip().split("\n")[:5]:  # name is almost always in the first few lines
        candidate_line = line.strip()
        # Heuristic: 2-4 words, mostly alphabetic, no @ or digits — looks like "Jane Doe"
        words = candidate_line.split()
        if 1 < len(words) <= 4 and all(w.replace(".", "").isalpha() for w in words):
            name = candidate_line
            break

    return ExtractedIdentity(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
    )


def check_consistency(new_identity: ExtractedIdentity, existing_identity: ExtractedIdentity) -> Optional[str]:
    """
    Returns a warning message if the new resume looks like it belongs to a
    different person than the existing current resume, else None.
    Only compares fields present on BOTH sides — missing data isn't treated
    as a mismatch (a resume with no phone number shouldn't false-positive).
    """
    if existing_identity.email and new_identity.email:
        if existing_identity.email.lower() != new_identity.email.lower():
            return "Your new resume appears to contain different candidate information. Please verify before replacing your current resume."

    if existing_identity.name and new_identity.name:
        # loose match: at least one shared word (handles "Jane Doe" vs "Jane D." or middle-name variants)
        existing_words = set(w.lower() for w in existing_identity.name.split())
        new_words = set(w.lower() for w in new_identity.name.split())
        if not (existing_words & new_words):
            return "Your new resume appears to contain different candidate information. Please verify before replacing your current resume."

    return None
