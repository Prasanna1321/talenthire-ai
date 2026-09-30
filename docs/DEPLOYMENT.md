# TalentHire AI — Deployment Guide (Phase 8)

## Option A — Docker Compose (recommended for a demo / viva)

The fastest way to run the entire stack (PostgreSQL + FastAPI + React)
identically to production, in one command.

```bash
# From the project root
export GEMINI_API_KEY=your_key_here
export JWT_SECRET_KEY=$(openssl rand -hex 32)

docker compose up --build
```

- Frontend: http://localhost:5173
- Backend + Swagger docs: http://localhost:8000/docs
- The `db` service auto-runs `database/schema.sql` and `database/seed_data.sql`
  on first boot (via Postgres's `docker-entrypoint-initdb.d` convention).

Stop everything: `docker compose down` (add `-v` to also wipe the database volume).

---

## Option B — Cloud deployment (separate managed services)

A typical low-cost setup for a student/demo project:

| Component | Suggested service | Notes |
|---|---|---|
| PostgreSQL | Render / Railway / Neon / Supabase (managed Postgres) | Run `database/schema.sql` once via their SQL console or `psql` |
| Backend (FastAPI) | Render / Railway / Fly.io | Deploy `backend/` with `backend/Dockerfile`, or as a native Python service with `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Frontend (React) | Vercel / Netlify | Build command `npm run build`, output dir `dist/`, set `VITE`-time env or just point Axios `baseURL` at the deployed backend URL |
| File storage (resumes/audio) | Start on local disk (as shipped); swap to AWS S3 / Cloudinary for production scale | Only `save_uploaded_file()` / `save_audio_file()` in `app/services/*.py` need to change — the rest of the app is storage-agnostic |

### Environment variables to set in production

Backend:
```
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<db>
JWT_SECRET_KEY=<long random string — never reuse the .env.example placeholder>
GEMINI_API_KEY=<your production Gemini key>
FRONTEND_ORIGIN=https://your-frontend-domain.com
```

Frontend: none required at build time in this setup (the Vite dev proxy is
dev-only); for production, either serve the frontend behind the same
domain/reverse-proxy as the backend (see `frontend/nginx.conf`) or update
`src/api/axiosClient.js`'s `baseURL` to the deployed backend's full URL.

### Production checklist

- [ ] Rotate `JWT_SECRET_KEY` — never ship the `.env.example` default
- [ ] Run `database/schema.sql` against the production database (skip `seed_data.sql`)
- [ ] Set `FRONTEND_ORIGIN` to the real deployed frontend URL (CORS)
- [ ] Put a real `GEMINI_API_KEY` in the backend's environment (not committed to git)
- [ ] Enable HTTPS (most PaaS providers do this automatically)
- [ ] Point resume/audio storage at durable, non-ephemeral storage (S3, etc.) if the platform's filesystem resets on redeploy
- [ ] Consider adding rate limiting in front of `/api/auth/login` and `/api/resumes/upload`

---

## Running the test suite before deploying

```bash
cd backend
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/talenthire_test_db
pytest tests/ -v
```

All 23 tests (auth, jobs/applications, resumes, mock interview flow) should
pass — this was verified during development against a real local
PostgreSQL instance, not just mocked.
