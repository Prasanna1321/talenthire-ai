"""
app/services/ats_service.py
-------------------------------
Phase 4: TalentHire AI ATS Compatibility Score — an explainable, non-fake
0-100 score computed from the resume's own extracted content (no black-box
model, no hardcoded category label). Belongs in: backend/app/services/ats_service.py

Weights (sum to 100):
    Skills relevance        30
    Experience signals      20
    Education present       10
    Projects present        15
    Keyword density         10
    Resume completeness     10
    Formatting/readability   5
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ATSResult:
    total_score: float
    breakdown: dict
    strengths: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


EDUCATION_MARKERS = ["b.e", "bachelor", "b.tech", "m.tech", "college", "university", "degree", "cgpa", "gpa", "school"]
EXPERIENCE_MARKERS = ["intern", "internship", "worked at", "experience", "employed", "years of experience", "company"]
PROJECT_MARKERS = ["project", "built", "developed", "designed and implemented", "github.com"]


def _score_skills(extracted_skills: List[str], job_required_skills: Optional[List[str]]) -> tuple[float, List[str]]:
    if not extracted_skills:
        return 0.0, []
    if job_required_skills:
        job_set = {s.lower() for s in job_required_skills}
        matched = [s for s in extracted_skills if s.lower() in job_set]
        ratio = len(matched) / max(1, len(job_set))
        missing = sorted(job_set - {s.lower() for s in extracted_skills})
        return round(min(ratio, 1.0) * 30, 2), missing
    # No specific job targeted — score by breadth of skills found (capped)
    breadth_ratio = min(len(extracted_skills) / 10, 1.0)
    return round(breadth_ratio * 30, 2), []


def _score_presence(text: str, markers: List[str], max_points: float) -> float:
    lowered = text.lower()
    hits = sum(1 for m in markers if m in lowered)
    ratio = min(hits / 2, 1.0)  # 2+ marker hits = full credit
    return round(ratio * max_points, 2)


def _score_completeness(text: str, email: Optional[str], phone: Optional[str]) -> float:
    points = 0.0
    if email:
        points += 4
    if phone:
        points += 3
    if len(text.split()) > 150:  # a very sparse resume can't be "complete"
        points += 3
    return round(points, 2)


def _score_formatting(text: str) -> float:
    """Cheap heuristic: penalize walls of text with no line breaks, reward reasonable structure."""
    lines = [l for l in text.split("\n") if l.strip()]
    if not lines:
        return 0.0
    avg_line_len = sum(len(l) for l in lines) / len(lines)
    if avg_line_len < 120:  # not one giant unbroken paragraph
        return 5.0
    if avg_line_len < 200:
        return 3.0
    return 1.0


def _score_keyword_density(text: str, job_required_skills: Optional[List[str]]) -> float:
    if not job_required_skills:
        return 5.0  # neutral partial credit when there's no specific job to target
    lowered = text.lower()
    hits = sum(1 for kw in job_required_skills if kw.lower() in lowered)
    ratio = hits / max(1, len(job_required_skills))
    return round(ratio * 10, 2)


def compute_ats_score(
    resume_text: str,
    extracted_skills: List[str],
    job_required_skills: Optional[List[str]] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> ATSResult:
    skills_score, missing_keywords = _score_skills(extracted_skills, job_required_skills)
    experience_score = _score_presence(resume_text, EXPERIENCE_MARKERS, 20)
    education_score = _score_presence(resume_text, EDUCATION_MARKERS, 10)
    projects_score = _score_presence(resume_text, PROJECT_MARKERS, 15)
    keyword_score = _score_keyword_density(resume_text, job_required_skills)
    completeness_score = _score_completeness(resume_text, email, phone)
    formatting_score = _score_formatting(resume_text)

    breakdown = {
        "skills_match": skills_score,        # /30
        "experience": experience_score,      # /20
        "education": education_score,        # /10
        "projects": projects_score,          # /15
        "keywords": keyword_score,           # /10
        "completeness": completeness_score,  # /10
        "formatting": formatting_score,      # /5
    }

    strengths = []
    suggestions = []
    if skills_score >= 20:
        strengths.append("Strong, clearly listed technical skills.")
    elif skills_score < 10:
        suggestions.append("List more specific technical skills relevant to your target role.")
    if projects_score >= 10:
        strengths.append("Concrete projects are described.")
    else:
        suggestions.append("Add a Projects section describing what you built and the tools used.")
    if experience_score < 8:
        suggestions.append("Mention internships or hands-on experience, even coursework-based, explicitly.")
    if completeness_score < 7:
        suggestions.append("Make sure your email and phone number are clearly visible on the resume.")

    return ATSResult(
        total_score=round(sum(breakdown.values()), 2),
        breakdown=breakdown,
        strengths=strengths,
        missing_keywords=missing_keywords,
        suggestions=suggestions,
    )
