"""
app/config.py
--------------
Centralized application settings, loaded from environment variables (.env).
Belongs in: backend/app/config.py

Uses pydantic-settings so every config value is typed and validated at
startup instead of failing deep inside some unrelated module later.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/talenthire_db"

    # --- JWT ---
    JWT_SECRET_KEY: str = "dev_secret_change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Gemini (question generation + feedback) ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-flash-latest"

    # --- EmailJS (OTP + notification emails) ---
    EMAILJS_SERVICE_ID: str = ""
    EMAILJS_TEMPLATE_ID: str = ""
    EMAILJS_PUBLIC_KEY: str = ""
    EMAILJS_PRIVATE_KEY: str = ""

    # --- Gemini Live API (voice interview) ---
    # Reuses GEMINI_API_KEY above.
    GEMINI_LIVE_MODEL: str = "gemini-2.0-flash-exp"

    # --- App URLs (used in emails and CORS) ---
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # --- CORS ---
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- File storage ---
    RESUME_UPLOAD_DIR: str = "uploads/resumes"
    AUDIO_UPLOAD_DIR: str = "uploads/audio"

    # --- ML model ---
    RESUME_MODEL_PATH: str = "../ml/resume_classifier/resume_model.pkl"

    # --- Environment configuration ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Singleton settings instance imported everywhere else in the app
settings = Settings()