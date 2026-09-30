# TalentHire AI

**Cloud-Based Intelligent Interview Evaluation System Using Machine Learning and Generative AI**

A final-year B.E. major project (Computer Science and Design, VTU Belagavi —
PES Institute of Technology & Management, Shivamogga) that automates
resume screening, generates role-based interview questions, captures and
transcribes spoken answers, evaluates responses with NLP, and produces
AI-generated personalized feedback — for both candidates preparing for
interviews and recruiters running preliminary candidate assessment.

> Built against the project's report (Problem Statement, Objectives,
> Scope, Methodology, System Design) with the explicitly requested tech
> stack: **React + FastAPI + PostgreSQL + scikit-learn + Gemini + Whisper**.

---

## Features

| Module | What it does |
|---|---|
| **User Authentication** | JWT-based register/login for Candidate, Recruiter, Admin roles |
| **Candidate / Recruiter / Admin Dashboards** | Role-specific summary stats and quick actions |
| **Resume Upload & Parser** | PDF → text (PyMuPDF) → skill extraction (spaCy + SkillNER) |
| **Resume Classification** | TF-IDF + RandomForest model classifies resumes into domain categories |
| **Job Recommendation** | Ranks open jobs against a candidate's extracted skills |
| **AI Question Generator** | Gemini generates role/skill-based interview questions + reference answers |
| **Mock Interview** | Full session flow: start → answer → score → complete → feedback |
| **Speech Recognition** | OpenAI Whisper transcribes recorded spoken answers |
| **Answer Evaluation** | Sentence-Transformers + cosine similarity + NLP heuristics score each answer |
| **AI Feedback** | Gemini turns the full Q&A transcript into strengths/improvements/rating |
| **Interview Reports** | Aggregated per-session report: answers, scores, feedback |
| **Recruiter Analytics** | Hiring funnel metrics, average candidate scores, top in-demand skills |

---

## Tech Stack

- **Frontend:** React.js, Vite, Tailwind CSS, Axios, React Router
- **Backend:** Python, FastAPI, SQLAlchemy, JWT
- **Database:** PostgreSQL (pgAdmin-compatible)
- **AI/ML:** spaCy, PyMuPDF, SkillNER, Sentence-Transformers, scikit-learn
  (RandomForest), Google Gemini API, OpenAI Whisper

---

## Project Structure

```
talenthire-ai/
├── frontend/          React + Vite + Tailwind SPA
│   └── src/
│       ├── api/        Axios service modules (one per domain)
│       ├── context/     AuthContext (JWT session state)
│       ├── routes/       ProtectedRoute (auth + role guards)
│       ├── components/    Shared UI (Navbar, Sidebar, cards, badges...)
│       └── pages/          candidate/ · recruiter/ · admin/ · auth/
├── backend/            FastAPI REST API (MVC-style)
│   └── app/
│       ├── models/       SQLAlchemy ORM (12 tables)
│       ├── schemas/       Pydantic request/response contracts
│       ├── routers/        Controllers — one file per module
│       ├── services/        Business logic, calls into ml/
│       ├── core/             JWT security + role guards
│       └── main.py            App entrypoint
│   └── tests/           pytest suite (23 tests, run against real PostgreSQL)
├── ml/                 Standalone, independently-runnable AI modules
│   ├── resume_parser/          PyMuPDF + spaCy + SkillNER + SBERT
│   ├── resume_classifier/       dataset_generator.py, train_model.py, resume_model.pkl
│   ├── question_generator/       Gemini
│   ├── speech_recognition/        Whisper
│   ├── answer_evaluator/           SBERT + cosine similarity
│   └── feedback_generator/          Gemini
├── database/            schema.sql (12 tables) + seed_data.sql
├── docs/               ARCHITECTURE.md · API_DOCUMENTATION.md · INSTALLATION.md · DEPLOYMENT.md
└── docker-compose.yml   Full-stack local/prod orchestration
```

---

## Quickstart

```bash
# 1. Database
psql -U postgres -c "CREATE DATABASE talenthire_db;"
psql -U postgres -d talenthire_db -f database/schema.sql

# 2. Backend
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env   # then fill in DATABASE_URL, JWT_SECRET_KEY, GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** → register a Recruiter and a Candidate
account → post a job → generate AI questions → take a mock interview →
view your AI feedback report.

Or skip all of the above and run `docker compose up --build` from the
project root (see `docs/DEPLOYMENT.md`).

Full setup details: **[docs/INSTALLATION.md](docs/INSTALLATION.md)**

---

## Documentation

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — system layers, request flows, design decisions
- **[docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** — all 36 REST endpoints with examples
- **[docs/INSTALLATION.md](docs/INSTALLATION.md)** — local dev setup, troubleshooting
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** — Docker Compose + cloud deployment
- Live interactive API docs once the backend is running: `http://localhost:8000/docs`

---

## Development Phases (as delivered)

1. ✅ Folder structure — `frontend/ backend/ ml/ database/ docs/`
2. ✅ Database — 12-table PostgreSQL schema, indexes, triggers, seed data (verified with real `psql` run)
3. ✅ Backend APIs — full MVC REST API, JWT auth, role-based access control
4. ✅ Frontend — React/Vite/Tailwind SPA, all 3 dashboards, all listed pages (builds clean with `npm run build`)
5. ✅ ML Model — resume classifier trained on a labeled dataset, `resume_model.pkl` saved and committed
6. ✅ AI Integration — Gemini (questions + feedback), Whisper (speech-to-text), Sentence-Transformers (answer scoring)
7. ✅ Testing — 23 pytest tests covering auth, jobs, applications, resumes, and the full mock-interview flow, passing against a real PostgreSQL database
8. ✅ Deployment — Dockerfiles + docker-compose.yml + cloud deployment guide

---

## Notes on scope decisions

- The report's architecture diagram lists Django REST + OpenAI/GPT + AWS
  S3; this build follows the **explicit tech-stack instructions**
  (FastAPI + SQLAlchemy + Gemini) instead, since those were given as
  direct requirements. File storage is implemented locally but written
  so only two functions (`save_uploaded_file`, `save_audio_file`) need to
  change to point at S3 or another object store later.
- No real-world labeled resume dataset was provided, so
  `ml/resume_classifier/dataset_generator.py` builds a representative
  synthetic dataset from domain skill templates — a standard, disclosed
  approach for this kind of academic ML pipeline. Swap in a real CSV
  (e.g. a public Kaggle resume dataset) and re-run `train_model.py` to
  retrain on real data; the pipeline doesn't need any other changes.
- As stated in the report's Scope, this project does **not** implement
  final autonomous hiring decisions, webcam-based proctoring/surveillance,
  or large-scale enterprise benchmarking — it focuses on preliminary
  AI-assisted screening and candidate interview preparation.

---

## Academic Context

**Department of Computer Science and Design**
PES Institute of Technology & Management, Shivamogga — VTU Belagavi, 2025–2026

Contributes to **SDG 4** (Quality Education — structured AI interview
practice), **SDG 8** (Decent Work and Economic Growth — fairer, faster
preliminary hiring support), and **SDG 9** (Industry, Innovation and
Infrastructure — ML/NLP/cloud-based recruitment tooling).
