# TalentHire AI — API Documentation

Base URL (local dev): `http://localhost:8000`
Interactive docs (auto-generated from the code, always up to date):
**Swagger UI** → `/docs` · **ReDoc** → `/redoc` · **OpenAPI JSON** → `/openapi.json`

All endpoints below are prefixed with `/api` except health checks.
Authenticated endpoints require an `Authorization: Bearer <access_token>` header.

---

## Authentication (`/api/auth`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Register as candidate, recruiter, or admin |
| POST | `/api/auth/login` | Public | Login with email + password, returns JWT pair |
| POST | `/api/auth/refresh` | Public (valid refresh token) | Exchange a refresh token for a new access token |

**Register request:**
```json
{
  "full_name": "Praveen Kumar",
  "email": "praveen@example.com",
  "password": "SecurePass123!",
  "role": "candidate",
  "phone": "9876543210",
  "location": "Shivamogga, Karnataka"
}
```
For `role: "recruiter"`, `company_name` is required instead of `phone`/`location`.

**Login/Register response:**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "role": "candidate",
  "user_id": 1,
  "full_name": "Praveen Kumar"
}
```
Access tokens expire in 60 minutes; refresh tokens in 7 days (configurable via `.env`).

---

## Users & Dashboards (`/api/users`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/users/me` | Any authenticated | Current user's basic info |
| GET | `/api/users/candidate/profile` | Candidate | Get candidate profile |
| PUT | `/api/users/candidate/profile` | Candidate | Update candidate profile |
| GET | `/api/users/candidate/dashboard` | Candidate | Summary stats for Candidate Dashboard |
| GET | `/api/users/recruiter/profile` | Recruiter | Get recruiter profile |
| GET | `/api/users/recruiter/dashboard` | Recruiter | Summary stats for Recruiter Dashboard |

---

## Jobs (`/api/jobs`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/jobs` | Recruiter | Post a new job |
| GET | `/api/jobs?status=open&location=...` | Any authenticated | Browse jobs (filterable) |
| GET | `/api/jobs/{job_id}` | Any authenticated | Get one job |
| PUT | `/api/jobs/{job_id}` | Recruiter (owner) | Update a job |
| DELETE | `/api/jobs/{job_id}` | Recruiter (owner) | Delete a job |
| GET | `/api/jobs/recruiter/mine` | Recruiter | List jobs I posted |

**Create job request:**
```json
{
  "title": "Gen AI Engineer Intern",
  "description": "Work on LLM-based products and RAG pipelines.",
  "required_skills": ["Python", "LLM", "Prompt Engineering", "FastAPI"],
  "experience_level": "entry",
  "location": "Bengaluru, India",
  "job_type": "internship"
}
```

---

## Applications (`/api/applications`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/applications` | Candidate | Apply to a job (auto-computes skill match score) |
| GET | `/api/applications/candidate/mine` | Candidate | My applications |
| GET | `/api/applications/job/{job_id}` | Recruiter (owner) | Applicants for a job, ranked by match score |
| PUT | `/api/applications/{id}/status` | Recruiter (owner) | Update status: `applied → shortlisted → interview_scheduled → interview_completed → selected/rejected` |

---

## Resumes (`/api/resumes`) — Resume Upload, Parser, Classification, Job Recommendation

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/resumes/upload` | Candidate | Upload PDF → auto-parse (PyMuPDF+spaCy+SkillNER) → auto-classify (RandomForest) |
| GET | `/api/resumes/mine` | Candidate | List my resumes with extracted skills/category |
| GET | `/api/resumes/{resume_id}` | Candidate (owner) | Get one resume's parsed data |
| GET | `/api/resumes/recommendations/jobs` | Candidate | AI job recommendations ranked by skill-overlap match score |

Upload is `multipart/form-data` with a `file` field (PDF only).

**Resume response:**
```json
{
  "resume_id": 4,
  "candidate_id": 2,
  "original_filename": "resume.pdf",
  "extracted_skills": ["python", "fastapi", "machine learning", "llm"],
  "predicted_category": "Generative AI / LLM Engineering",
  "prediction_confidence": 0.94,
  "uploaded_at": "2026-07-18T10:15:00Z"
}
```

---

## Interviews (`/api/interviews`) — Question Generator, Mock Interview, Speech, Evaluation, Feedback, Reports

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/interviews/questions/generate` | Recruiter/Admin | Generate + store N Gemini questions for a job or free-text role |
| GET | `/api/interviews/questions/job/{job_id}` | Any authenticated | List questions for a job |
| POST | `/api/interviews/sessions/start` | Candidate | Start a mock/official interview session |
| GET | `/api/interviews/sessions/mine` | Candidate | My session history |
| POST | `/api/interviews/sessions/{id}/answer/audio` | Candidate | Submit a recorded answer (`multipart/form-data`, `audio_file` + `question_id` query param) → Whisper transcription → auto-scored |
| POST | `/api/interviews/sessions/{id}/answer/text` | Candidate | Submit a typed answer → auto-scored |
| POST | `/api/interviews/sessions/{id}/complete` | Candidate | Mark session complete → generates Gemini feedback report |
| GET | `/api/interviews/sessions/{id}/report` | Candidate/Recruiter/Admin | Full report: all answers, scores, and feedback |

**Generate questions request:**
```json
{ "job_id": 3, "num_questions": 5, "difficulty": "mixed" }
```

**Score response (per answer):**
```json
{
  "score_id": 12,
  "answer_id": 30,
  "similarity_score": 0.81,
  "relevance_score": 81.0,
  "fluency_score": 76.5,
  "confidence_score": 90.0,
  "final_score": 82.06
}
```
`final_score = 0.55×relevance + 0.25×fluency + 0.20×confidence` (see
`ml/answer_evaluator/evaluator.py`).

---

## Recruiter Analytics (`/api/analytics`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/analytics/recruiter` | Recruiter | Jobs posted, applications, interviews conducted, average candidate score, top in-demand skills |

---

## Notifications (`/api/notifications`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/notifications/mine` | Any authenticated | My notifications |
| PUT | `/api/notifications/{id}/read` | Any authenticated | Mark one as read |
| PUT | `/api/notifications/read-all` | Any authenticated | Mark all as read |

---

## Admin (`/api/admin`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/admin/users` | Admin | List all users |
| PUT | `/api/admin/users/{id}/status?is_active=true|false` | Admin | Activate/deactivate a user |
| GET | `/api/admin/dashboard` | Admin | System-wide stats |

---

## Error format

All errors follow FastAPI's standard shape:
```json
{ "detail": "Human-readable error message" }
```
Common status codes: `400` (validation/business rule), `401` (missing/invalid
token), `403` (wrong role or not the resource owner), `404` (not found).
