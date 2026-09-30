# Belongs in: backend/Dockerfile
# NOTE: build this with the PROJECT ROOT as the build context (see the
# docker-compose.yml at the project root), because the image needs both
# backend/ and ml/ — e.g.:
#   docker build -f backend/Dockerfile -t talenthire-backend .
FROM python:3.11-slim

WORKDIR /app

# System deps needed by psycopg2, PyMuPDF, spaCy, and Whisper/ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt \
    && python -m spacy download en_core_web_sm

# Copy backend app code and the ml/ package it imports at runtime
COPY backend/app ./backend/app
COPY ml ./ml

WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
