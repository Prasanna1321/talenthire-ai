# TalentHire AI — Architecture

## System layers

This implementation maps directly onto the layered architecture from the
project report (Section 3.2), with the report's Django/OpenAI/AWS choices
substituted for the project's actual required stack — **FastAPI, Gemini,
and local/S3-ready file storage** — per the explicit tech-stack instructions.

```
┌─────────────────────────────────────────────────────────────────┐
│  USER LAYER            Candidate · Recruiter · Admin             │
└───────────────────────────────┬───────────────────────────────────┘
┌───────────────────────────────▼───────────────────────────────────┐
│  FRONTEND (React 18 + Vite + Tailwind CSS + React Router + Axios)  │
│  - Role-based dashboards & protected routes                        │
│  - JWT stored client-side, auto-refreshed via Axios interceptor    │
└───────────────────────────────┬───────────────────────────────────┘
                                 │ REST (JSON / multipart)
┌───────────────────────────────▼───────────────────────────────────┐
│  BACKEND CONTROL LAYER (FastAPI)                                   │
│  routers/  → thin controllers (auth, jobs, resumes, interviews...) │
│  services/ → business logic, orchestrates DB + ML calls            │
│  core/     → JWT security, role-based dependency guards            │
│  models/   → SQLAlchemy ORM (12 tables)                            │
│  schemas/  → Pydantic request/response contracts                   │
└───────┬───────────────────────────────────────────┬───────────────┘
        │                                            │
┌───────▼─────────────────┐          ┌───────────────▼───────────────┐
│  DATA LAYER              │          │  AI SERVICES PROCESSING LAYER  │
│  PostgreSQL (pgAdmin)    │          │  ml/resume_parser  (PyMuPDF,   │
│  - users, jobs, resumes, │          │    spaCy, SkillNER, SBERT)     │
│    applications,         │          │  ml/resume_classifier          │
│    interview_sessions,   │          │    (TF-IDF + RandomForest)     │
│    answers, scores,      │          │  ml/question_generator         │
│    feedback,             │          │    (Gemini API)                │
│    notifications, ...    │          │  ml/speech_recognition         │
│  Local/S3-ready file     │          │    (OpenAI Whisper)            │
│  storage for resumes     │          │  ml/answer_evaluator            │
│  + interview audio       │          │    (SBERT + cosine similarity) │
│                           │          │  ml/feedback_generator          │
│                           │          │    (Gemini API)                │
└───────────────────────────┘          └─────────────────────────────┘
```

## Why FastAPI services call into `ml/` directly (no separate microservice)

For a project of this scope, running the ML pipeline as in-process Python
calls (rather than a separate model-serving microservice) keeps deployment
simple while still preserving a clean **module boundary**: everything in
`ml/` is independently runnable/testable (see `ml/resume_classifier/train_model.py`),
and `backend/app/services/*.py` is the only place that imports from `ml/`.
If this needed to scale to a dedicated inference service later, only the
service layer would change — routers and the database layer are unaffected.

ML imports are **lazy** (imported inside functions, not at module load
time) specifically so the rest of the API — auth, jobs, applications,
dashboards — stays fully operational and testable even before the heavier
ML dependencies (spaCy, sentence-transformers, Whisper) are installed or
configured. See the comments in `app/services/resume_service.py` and
`app/services/interview_service.py`.

## Request flow: Mock Interview (end-to-end example)

1. **Recruiter** posts a job → `POST /api/jobs`
2. **Recruiter** triggers `POST /api/interviews/questions/generate` →
   `interview_service.generate_and_store_questions()` calls
   `ml/question_generator` (Gemini) → rows inserted into `interview_questions`
3. **Candidate** starts a session → `POST /api/interviews/sessions/start`
   → new `interview_sessions` row (`status=in_progress`)
4. **Candidate** answers each question:
   - Typed: `POST .../answer/text` → `Answer` row created directly
   - Spoken: `POST .../answer/audio` → audio saved → `ml/speech_recognition`
     (Whisper) transcribes → `Answer.transcribed_text` populated
   - Either path then calls `ml/answer_evaluator` (SBERT cosine similarity
     vs. the question's `ideal_answer`) → a `Score` row is created
5. **Candidate** finishes → `POST .../complete` → session marked
   `completed` → `interview_service.generate_session_feedback()` sends the
   full Q&A + scores transcript to `ml/feedback_generator` (Gemini) →
   a `Feedback` row is created
6. **Candidate/Recruiter** views `GET .../report` → aggregates session +
   answers + scores + feedback into one response

## Database design notes

- `users` is the single identity table; `candidates` and `recruiters` are
  1-to-1 profile extensions (not subclassed via table inheritance) —
  simpler joins, and `role` on `users` is the source of truth for RBAC.
- `resumes.embedding` and `resumes.extracted_skills` use PostgreSQL's
  native `ARRAY` type rather than a separate join table, since they're
  always read/written as a whole unit per resume (no per-skill querying
  needed at this project's scale).
- `Application.match_score` and `JobRecommendation.match_score` are both
  computed from the same `compute_skill_match_score()` function
  (simple, explainable overlap-percentage — deliberately not a black-box
  score, so recruiters/candidates can trust and understand it).
- Cascade deletes are used throughout (`ondelete="CASCADE"`) so deleting a
  user cleanly removes their downstream data (applications, resumes,
  sessions, etc.) without orphaned rows.

## Security

- Passwords hashed with **bcrypt** directly (not the unmaintained `passlib`
  wrapper — see `app/core/security.py` for why).
- JWT access tokens (60 min) + refresh tokens (7 days), role embedded in
  the token payload and re-validated against the DB on every request
  (`core/dependencies.get_current_user`).
- Role-based route guards via `core/dependencies.require_role(...)`, and
  ownership checks (e.g. a recruiter can only view/edit their own jobs)
  are enforced in the router/service layer, not just at the role level.
