"""
app/main.py
------------
FastAPI application entrypoint. Belongs in: backend/app/main.py

Run with:
    uvicorn app.main:app --reload --port 8000

Interactive API docs (Swagger UI): http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401 - ensures all models are registered on Base.metadata

from app.routers import auth, users, jobs, applications, resumes, interviews, analytics, notifications, admin, aptitude, voice_interview


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Creates any missing tables on startup (safe no-op if schema.sql was
    already applied manually via psql/pgAdmin — SQLAlchemy's create_all
    only creates tables that don't yet exist).
    """
    Base.metadata.create_all(bind=engine)
    yield
    # (no teardown work needed; the DB connection pool closes with the process)


app = FastAPI(
    title="TalentHire AI",
    description=(
        "Cloud-Based Intelligent Interview Evaluation System Using Machine "
        "Learning and Generative AI — REST API"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS: allow the Vite frontend dev server (and prod origin) to call the API ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register all routers (each maps to one or more project "modules") ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(resumes.router)
app.include_router(interviews.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(aptitude.router)
app.include_router(voice_interview.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "TalentHire AI API", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
