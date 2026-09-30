"""
app/routers/voice_interview.py
----------------------------------
Phase 6: real-time AI voice interview via Google's GEMINI LIVE API.

*** IMPORTANT — READ BEFORE USING ***
This is written against Gemini Live API's ephemeral-token pattern as
documented at the time this was written. Google updates model names and
API details periodically — before relying on this, check
https://ai.google.dev/gemini-api/docs/live and
https://ai.google.dev/gemini-api/docs/ephemeral-tokens for the CURRENT
model name (GEMINI_LIVE_MODEL in config.py) and token-creation method.

Why Gemini Live instead of OpenAI Realtime: it reuses the SAME
GEMINI_API_KEY already used for question generation and feedback — no
separate account, no separate billing, and it has a genuine free tier
(unlike OpenAI's Realtime API, which is paid-only with no free quota).

Security: GEMINI_API_KEY is used here, server-side, to mint a short-lived
ephemeral token. Only that ephemeral token is returned to the frontend —
the real key never reaches the browser. The frontend uses the ephemeral
token to open its own WebSocket connection directly to Gemini's Live API.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User
from app.models.profile import Candidate
from app.models.resume import Resume
from app.models.job import Job

router = APIRouter(prefix="/api/interview/voice", tags=["Voice Interview (Phase 6)"])


def _build_interview_instructions(candidate_name: str, resume_skills: list[str], job) -> str:
    """Same prompt-building approach as the existing Gemini question generator —
    grounds questions in the candidate's actual resume, not generic filler."""
    skills_line = ", ".join(resume_skills) if resume_skills else "General Software Engineering, Python, Web Development"
    job_line = f"{job.title}: {job.description}" if job else "Software Engineer"
    required_skills_line = ", ".join(job.required_skills) if (job and job.required_skills) else "Problem Solving, System Design"

    return f"""You are TalentHire AI, an intelligent, human-like AI interviewer (speaking naturally like Siri, Alexa, or Gemini Voice).
You are conducting a live interview with candidate {candidate_name} for the role of {job_line}.

CANDIDATE'S RESUME SKILLS: {skills_line}
JOB REQUIRED SKILLS: {required_skills_line}

IMPORTANT INTERVIEW DIRECTIVES:
1. Greet {candidate_name} warmly by name and introduce yourself as TalentHire AI.
2. Ask questions based directly on the candidate's uploaded resume skills ({skills_line}) and the job position ({job_line}).
3. Ask ONE question at a time. Keep your turns clear, spoken naturally like a real human interviewer.
4. Listen to the candidate's answer, acknowledge their response with human-like conversation, and adapt your next follow-up question based on what they said.
5. Never monologue. Keep each turn under 3 sentences."""


@router.post("/session-token")
def create_voice_session_token(
    job_id: int | None = None,
    current_user: User = Depends(require_role("candidate")),
    db: Session = Depends(get_db),
):
    """
    Mints a short-lived ephemeral token via the Gemini Live API using the
    real GEMINI_API_KEY (server-side only), returns just the ephemeral
    token + model name + system instructions to the frontend so it can
    open its own WebSocket session directly with Gemini.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured on the server.")

    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate.candidate_id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    job = db.query(Job).filter(Job.job_id == job_id).first() if job_id else None

    instructions = _build_interview_instructions(
        candidate_name=current_user.full_name,
        resume_skills=resume.extracted_skills if (resume and resume.extracted_skills) else [],
        job=job,
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Ephemeral tokens: short expiry window is intentional — the token
        # is only meant to live long enough for the frontend to open its
        # WebSocket connection and run one interview session.
        now = datetime.now(timezone.utc)
        token = client.auth_tokens.create(
            config=types.CreateAuthTokenConfig(
                uses=1,
                expire_time=(now + timedelta(minutes=30)).isoformat(),
                new_session_expire_time=(now + timedelta(minutes=2)).isoformat(),
            )
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="google-genai SDK not installed. Run: pip install google-genai",
        )
    except Exception as exc:  # noqa: BLE001 — surface the real Gemini error to help debugging
        raise HTTPException(status_code=502, detail=f"Could not create Gemini Live ephemeral token: {exc}")

    return {
        "token": token.name,
        "model": settings.GEMINI_LIVE_MODEL,
        "instructions": instructions,
        "skills": resume.extracted_skills if (resume and resume.extracted_skills) else [],
    }
