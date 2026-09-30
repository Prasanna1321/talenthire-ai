# TalentHire AI — Complete Setup Guide (Unzip to Fully Working)

This is the **full, current** setup guide covering everything built so far
(Phases 1–8, plus Phase 6 scaffolding). Follow it top to bottom on a fresh
machine and you'll have the complete app running.

---

## Part 0 — What you need before starting

| Tool | Version | Download |
|---|---|---|
| Python | 3.11+ | https://python.org/downloads (check "Add python.exe to PATH" on Windows) |
| Node.js | 18+ LTS | https://nodejs.org |
| PostgreSQL | 16 | https://www.postgresql.org/download (includes pgAdmin) |
| VS Code (recommended) | latest | https://code.visualstudio.com |

Accounts you'll need:
- **Google Gemini API key** (free) — https://aistudio.google.com/app/apikey — powers question generation, feedback, AND the Phase 6 voice interview (Gemini Live reuses this same key)
- **Resend API key** (free tier) — https://resend.com — powers OTP verification emails and recruiter approval notifications. The app works without this too — emails just won't actually send, they'll log to the backend console instead, which is fine for local testing.

You do **not** need an OpenAI account — Phase 6 was rebuilt to use Gemini's Live API instead, which reuses your existing Gemini key.

---

## Part 1 — Unzip and open the project

1. Extract `talenthire-ai.zip` to a simple path, e.g. `C:\Projects\talenthire-ai` (Windows) or `~/Projects/talenthire-ai` (Mac/Linux)
2. Open the folder in VS Code: **File → Open Folder**

You should see: `backend/`, `frontend/`, `ml/`, `database/`, `docs/`, `docker-compose.yml`, `README.md`

---

## Part 2 — Database setup

### Option A — pgAdmin (GUI, easiest)

1. Open **pgAdmin 4**, connect to your local PostgreSQL server
2. Right-click **Databases → Create → Database** → name it `talenthire_db` → Save
3. Right-click `talenthire_db` → **Query Tool**
4. Open `database/schema.sql` in VS Code, copy all, paste into the Query Tool, click **Execute (▶)**
   - This creates all tables for every phase: users, jobs, resumes, interviews, OTPs, recruiter approval, aptitude tests, everything
5. (Optional) Repeat with `database/seed_data.sql` for demo job/user data

### Option B — command line

```bash
psql -U postgres -c "CREATE DATABASE talenthire_db;"
psql -U postgres -d talenthire_db -f database/schema.sql
psql -U postgres -d talenthire_db -f database/seed_data.sql   # optional demo data
```

### Seed the aptitude question bank (REQUIRED — the app will error without this)

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install sqlalchemy psycopg2-binary pydantic pydantic-settings python-dotenv
python ../database/seed_aptitude_questions.py
```
This inserts 75 questions (15 per category) so the 30-question test can pull a random set each time. You'll see `Inserted 75 aptitude questions.`

---

## Part 3 — Backend setup

Still inside `backend/` with the venv active:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

This installs a lot (spaCy, sentence-transformers/PyTorch, Whisper, Gemini SDKs, reportlab for PDFs). It can take 10–20 minutes on the first run — that's normal, don't cancel it.

**If `pip install -r requirements.txt` fails partway through:**
- Update pip first: `python -m pip install --upgrade pip`
- Install `setuptools wheel` first: `pip install setuptools wheel`
- If `openai-whisper` specifically fails: `pip install openai-whisper --no-build-isolation`
- Install everything else, then retry the one package that failed on its own

### Configure environment variables

```bash
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux
```

Open `backend/.env` and fill in:
```
DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@localhost:5432/talenthire_db
JWT_SECRET_KEY=any-long-random-string-you-make-up
GEMINI_API_KEY=your-real-gemini-key
GEMINI_MODEL=gemini-flash-latest
RESEND_API_KEY=your-real-resend-key-or-leave-placeholder
```

**If your DB password contains special characters** (`@`, `#`, `%`, etc.), URL-encode them in `DATABASE_URL` — e.g. a password `Pk@1321` becomes `Pk%401321` (the `@` is `%40`). Common encodings: `@`→`%40`, `#`→`%23`, `%`→`%25`.

### Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

Confirm it worked: open http://localhost:8000/docs — you should see the full Swagger API list (50+ endpoints across auth, jobs, resumes, interviews, aptitude, admin, voice).

---

## Part 4 — Frontend setup

Open a **second terminal** (keep the backend running in the first):

```bash
cd frontend
npm install ogl
npm run dev
```

Open **http://localhost:5173** — you should see the animated Home Page with the orbit background and voice orb.

---

## Part 5 — Try the full flow, phase by phase

### 5a. Register + verify email (Phase 2)
1. Click **Get Started → I'm a Candidate**
2. Fill in the form, submit
3. You're redirected to a 6-digit code screen
4. **If RESEND_API_KEY is set**: check your email for the code
5. **If not set**: check the backend terminal — it prints `[email_service] RESEND_API_KEY not set — skipping email...` but the OTP was still generated. To get the actual code for testing without email, run this in a Python shell with your venv active:
   ```python
   # From backend/ with venv active:
   python -c "
   from app.database import SessionLocal
   from app.models.user import User
   from app.models.otp import EmailOTP
   db = SessionLocal()
   user = db.query(User).filter(User.email == 'YOUR_TEST_EMAIL').first()
   otp = db.query(EmailOTP).filter(EmailOTP.user_id == user.user_id).order_by(EmailOTP.created_at.desc()).first()
   print('OTP hash exists but is not human-readable — set RESEND_API_KEY to receive real codes, or check server logs if you added a debug print in otp_service.py')
   "
   ```
   **Simplest fix**: just get a free Resend key (takes 2 minutes) so real emails send — this is the intended path.

### 5b. Register a recruiter (Phase 3)
1. Register a second account as **Recruiter** (needs a company name)
2. Verify its email the same way
3. Log in — you'll see a **"pending approval"** screen instead of the dashboard. This is correct — recruiters need admin approval before posting jobs.

### 5c. Approve the recruiter as admin
1. Register a third account, but this time go directly to `http://localhost:5173/register?role=admin` (Admin isn't offered on the normal Get Started flow, by design)
2. Verify its email, log in
3. Go to **Recruiter Approvals** in the sidebar → **Approve** the pending recruiter

### 5d. Post a job and generate questions
1. Log back in as the recruiter (now approved)
2. **Manage Jobs → Post New Job**
3. Click **✨ Generate AI Questions** (uses your Gemini key)

### 5e. Upload a resume + see your ATS score (Phase 4)
1. Log in as the candidate
2. **Resume Upload** → choose a PDF
3. You'll see the **TalentHire AI ATS Compatibility Score** with a full breakdown (skills, experience, education, projects, keywords, completeness, formatting) — no fake classification label

### 5f. Take the aptitude test (Phase 5)
1. **Browse Jobs** → apply to the job
2. **Mock Interview** → select the job → **Start Mock Interview**
3. You'll be redirected to the **30-question Aptitude Test** first (this is enforced by the backend, not just the UI)
4. Answer all 30, submit, see your score
5. Continue to the actual mock interview

### 5g. Complete a mock interview + download the PDF report (Phase 7)
1. Answer the interview questions (typed, or recorded audio if you installed the ML packages)
2. Finish → view your AI feedback
3. **Interview Reports** → select the session → **📄 Download PDF**

### 5h. Recruiter views candidate scores (Phase 8)
1. Log back in as recruiter → **Manage Jobs** → **View Applicants** on your job
2. You'll see ATS score, aptitude %, and interview score together per candidate, plus matched/missing skills

### 5i. Try the real-time voice interview (Phase 6 — optional, best-effort)
1. As candidate, **Mock Interview** → **🎙 Try Real-Time AI Voice Interview (Beta)**
2. This uses Gemini Live API (same key, free tier) over a WebSocket
3. **This is the one part of the app I could not fully test myself** — if it doesn't connect, check the backend terminal for the exact error and the comments at the top of `backend/app/routers/voice_interview.py` and `frontend/src/pages/candidate/VoiceInterview.jsx`, which flag exactly what to verify against Google's current docs (model name, message field names)

---

## Part 6 — Running the ML pipeline standalone (optional)

The resume classifier model (`ml/resume_classifier/resume_model.pkl`) is already trained and included. To retrain it (e.g. on a real dataset instead of the included synthetic one):
```bash
cd ml/resume_classifier
python dataset_generator.py
python train_model.py
```

---

## Part 7 — Every-day startup (after initial setup)

```bash
# Terminal 1
cd backend
venv\Scripts\activate            # Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm run dev
```
PostgreSQL runs as a background service automatically — no manual start needed on Windows/Mac; on Linux run `sudo service postgresql start` if it's not already running.

---

## Part 8 — Docker alternative (skip Parts 2–4 entirely)

If you'd rather not install Python/Node/Postgres locally:
```bash
docker compose up --build
```
Frontend: http://localhost:5173 · Backend docs: http://localhost:8000/docs
You'll still need to add your `GEMINI_API_KEY` as an environment variable before running (see `docker-compose.yml` comments), and run the aptitude question seed script once against the containerized database.

---

## Troubleshooting quick-reference

| Symptom | Fix |
|---|---|
| `password authentication failed` on backend startup | Your `DATABASE_URL` password doesn't match Postgres, or has un-encoded special characters |
| `ModuleNotFoundError: No module named 'fitz'` etc. | `pip install -r requirements.txt` didn't finish — rerun it |
| Resume upload works but scoring errors | Heavy ML packages (`sentence-transformers`, `spacy`) not installed — see Part 3 |
| "models/gemini-X is not found" | Google retired that model name — check https://ai.google.dev/gemini-api/docs/models for the current one, update `GEMINI_MODEL` in `.env` |
| Aptitude test start fails with "question bank too small" | Run `python database/seed_aptitude_questions.py` (Part 2) |
| Recruiter can't post jobs | Check their status in Admin → Recruiter Approvals — must be "approved" |
| OTP emails don't arrive | `RESEND_API_KEY` not set in `.env`, or still the placeholder value |
| Voice interview won't connect | See Part 5i — this is the one unverified piece; check the backend terminal's exact error |

---

## What's real vs. what to verify yourself

**Fully built and tested (36/36 automated backend tests passing against real PostgreSQL, frontend builds clean):** Phases 1–5, 7, 8 — auth, OTP, recruiter approval, resume ATS scoring/versioning, aptitude test, PDF reports, recruiter analytics.

**Built but not independently testable by me:** Phase 6 (Gemini Live voice interview) — needs your own working Gemini key and a live browser session to confirm the WebSocket message format still matches Google's current docs. Everything else in the app does not depend on this working.
