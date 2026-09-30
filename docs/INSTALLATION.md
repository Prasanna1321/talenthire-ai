# TalentHire AI — Installation Guide

This guide covers a full **local development setup** (no Docker) so every
piece — database, backend, ML pipeline, and frontend — can be run and
understood independently. See `docs/DEPLOYMENT.md` for the Docker /
production path.

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | Backend + ML |
| Node.js | 18+ | Frontend (Vite) |
| PostgreSQL | 16+ | Database (pgAdmin optional GUI) |
| Git | any | Version control |

---

## 1. Clone and set up the database

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE talenthire_db;"

# Apply the schema (12 tables, indexes, triggers)
psql -U postgres -d talenthire_db -f database/schema.sql

# (Optional) load demo data
psql -U postgres -d talenthire_db -f database/seed_data.sql
```

Or open `database/schema.sql` in **pgAdmin**'s Query Tool and execute it
against a new `talenthire_db` database.

---

## 2. Backend setup (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm

cp .env.example .env
# Edit .env: set DATABASE_URL, JWT_SECRET_KEY, and GEMINI_API_KEY
```

Get a free Gemini API key at https://aistudio.google.com/app/apikey and
put it in `.env` as `GEMINI_API_KEY=...`.

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

The app also runs `Base.metadata.create_all()` on startup as a safety net,
so even if you skip step 1, tables will be created automatically (though
running `schema.sql` first is recommended since it also adds indexes,
constraints, and the `updated_at` trigger).

---

## 3. Train the ML resume classifier

The trained model (`ml/resume_classifier/resume_model.pkl`) is already
included in this repository, so this step is **optional** — only needed
if you want to retrain on a different/real dataset.

```bash
cd ml
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

cd resume_classifier
python dataset_generator.py   # generates dataset/resume_dataset.csv
python train_model.py         # trains RandomForest, saves resume_model.pkl
```

> To train on a **real** labeled dataset instead of the synthetic one,
> replace `dataset_generator.py`'s output with any CSV that has `text`
> and `category` columns, then re-run `train_model.py`.

---

## 4. Frontend setup (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173
- The Vite dev server proxies `/api/*` requests to `http://localhost:8000`
  (see `vite.config.js`), so no CORS configuration is needed in dev.

---

## 5. Try it end-to-end

1. Open http://localhost:5173/register
2. Create a **Recruiter** account (needs a company name) and a **Candidate**
   account (use two different browsers/incognito tabs, or log out between).
3. As the recruiter: post a job, then click **"Generate AI Questions"**
   (requires `GEMINI_API_KEY` to be set).
4. As the candidate: upload a resume PDF, browse jobs, apply, then start a
   **Mock Interview** for that job role and answer the questions.
5. View the AI-generated feedback report under **Interview Reports**.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'fitz'` | Run `pip install -r requirements.txt` inside `backend/` — PyMuPDF installs as `fitz`. |
| `GEMINI_API_KEY is not set` | Add a real key to `backend/.env` — question generation & feedback need it. |
| `password cannot be longer than 72 bytes` | Already fixed in this codebase — `app/core/security.py` calls `bcrypt` directly instead of the unmaintained `passlib` wrapper (see comment in `requirements.txt`). If you see this, make sure you're on the version of `security.py` in this repo. |
| Frontend shows CORS errors | Confirm `FRONTEND_ORIGIN` in `backend/.env` matches the URL you're browsing from (default `http://localhost:5173`). |
| `psycopg2` fails to install | Install PostgreSQL client dev headers: `apt install libpq-dev` (Linux) or use `psycopg2-binary` (already the default here). |
