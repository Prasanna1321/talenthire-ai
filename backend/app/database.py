"""
app/database.py
----------------
Sets up the SQLAlchemy engine, session factory, and declarative Base.
Belongs in: backend/app/database.py

Every model in app/models/ imports `Base` from here.
Every route/service that touches the DB depends on `get_db` for a session.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# The engine manages the actual connection pool to PostgreSQL
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Each request gets its own Session bound to this factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models inherit from this Base
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a DB session and guarantees it's closed
    after the request finishes, even if an exception is raised.

    Usage in a router:
        @router.get("/jobs")
        def list_jobs(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
