-- ============================================================================
-- TalentHire AI - PostgreSQL Database Schema
-- Cloud-Based Intelligent Interview Evaluation System
-- ============================================================================
-- Run this file in pgAdmin / psql to create the full schema:
--   psql -U postgres -d talenthire_db -f schema.sql
-- ============================================================================

-- Clean slate (safe to re-run during development)
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS scores CASCADE;
DROP TABLE IF EXISTS answers CASCADE;
DROP TABLE IF EXISTS interview_sessions CASCADE;
DROP TABLE IF EXISTS interview_questions CASCADE;
DROP TABLE IF EXISTS resumes CASCADE;
DROP TABLE IF EXISTS applications CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS candidates CASCADE;
DROP TABLE IF EXISTS recruiters CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- 1. USERS  -- master identity table for every actor in the system
-- ============================================================================
CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,          -- bcrypt hash, never plaintext
    role            VARCHAR(20) NOT NULL CHECK (role IN ('candidate', 'recruiter', 'admin')),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. RECRUITERS  -- extra profile data for users with role='recruiter'
-- ============================================================================
CREATE TABLE recruiters (
    recruiter_id    SERIAL PRIMARY KEY,
    user_id         INTEGER UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    company_name    VARCHAR(150) NOT NULL,
    designation     VARCHAR(100),
    company_website VARCHAR(255),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. CANDIDATES  -- extra profile data for users with role='candidate'
-- ============================================================================
CREATE TABLE candidates (
    candidate_id      SERIAL PRIMARY KEY,
    user_id           INTEGER UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    phone             VARCHAR(20),
    location          VARCHAR(100),
    highest_education VARCHAR(150),
    years_experience  NUMERIC(4,1) DEFAULT 0,
    linkedin_url      VARCHAR(255),
    github_url        VARCHAR(255),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 4. JOBS  -- postings created by recruiters
-- ============================================================================
CREATE TABLE jobs (
    job_id            SERIAL PRIMARY KEY,
    recruiter_id      INTEGER NOT NULL REFERENCES recruiters(recruiter_id) ON DELETE CASCADE,
    title             VARCHAR(150) NOT NULL,
    description       TEXT NOT NULL,
    required_skills   TEXT[] NOT NULL,               -- e.g. {'Python','React','SQL'}
    experience_level  VARCHAR(30) CHECK (experience_level IN ('entry', 'mid', 'senior')),
    location          VARCHAR(100),
    job_type          VARCHAR(30) DEFAULT 'full-time',
    status            VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'draft')),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 5. RESUMES  -- uploaded resume files + parsed/classified output
-- ============================================================================
CREATE TABLE resumes (
    resume_id         SERIAL PRIMARY KEY,
    candidate_id      INTEGER NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    file_path         VARCHAR(255) NOT NULL,          -- storage path / cloud URL
    original_filename VARCHAR(255),
    raw_text          TEXT,                           -- extracted via PyMuPDF
    extracted_skills  TEXT[],                          -- via spaCy + SkillNER
    predicted_category VARCHAR(100),                  -- output of resume_model.pkl
    prediction_confidence NUMERIC(5,4),
    embedding         DOUBLE PRECISION[],              -- sentence-transformer vector (for similarity search)
    uploaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 6. APPLICATIONS  -- candidate applying to a job
-- ============================================================================
CREATE TABLE applications (
    application_id    SERIAL PRIMARY KEY,
    candidate_id      INTEGER NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    job_id            INTEGER NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    resume_id         INTEGER REFERENCES resumes(resume_id) ON DELETE SET NULL,
    match_score       NUMERIC(5,2),                    -- job-fit score (skill overlap / embedding similarity)
    status            VARCHAR(30) DEFAULT 'applied' CHECK (
                          status IN ('applied','shortlisted','interview_scheduled',
                                     'interview_completed','selected','rejected')
                      ),
    applied_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (candidate_id, job_id)
);

-- ============================================================================
-- 7. INTERVIEW_QUESTIONS  -- bank of AI-generated (and static) questions per job
-- ============================================================================
CREATE TABLE interview_questions (
    question_id       SERIAL PRIMARY KEY,
    job_id            INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
    question_text     TEXT NOT NULL,
    question_type     VARCHAR(30) DEFAULT 'technical' CHECK (
                          question_type IN ('technical','behavioral','situational','coding')
                      ),
    difficulty        VARCHAR(20) DEFAULT 'medium' CHECK (difficulty IN ('easy','medium','hard')),
    ideal_answer      TEXT,                            -- reference answer used for cosine-similarity scoring
    generated_by      VARCHAR(20) DEFAULT 'gemini',     -- 'gemini' or 'manual'
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 8. INTERVIEW_SESSIONS  -- one mock/real interview attempt by a candidate
-- ============================================================================
CREATE TABLE interview_sessions (
    session_id        SERIAL PRIMARY KEY,
    application_id    INTEGER REFERENCES applications(application_id) ON DELETE CASCADE,
    candidate_id      INTEGER NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    job_id            INTEGER REFERENCES jobs(job_id) ON DELETE SET NULL,
    session_type      VARCHAR(20) DEFAULT 'mock' CHECK (session_type IN ('mock', 'official')),
    status            VARCHAR(20) DEFAULT 'in_progress' CHECK (
                          status IN ('in_progress','completed','abandoned')
                      ),
    started_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at      TIMESTAMP
);

-- ============================================================================
-- 9. ANSWERS  -- candidate's answer per question in a session (text + audio)
-- ============================================================================
CREATE TABLE answers (
    answer_id         SERIAL PRIMARY KEY,
    session_id        INTEGER NOT NULL REFERENCES interview_sessions(session_id) ON DELETE CASCADE,
    question_id       INTEGER NOT NULL REFERENCES interview_questions(question_id) ON DELETE CASCADE,
    audio_file_path   VARCHAR(255),                    -- raw recorded audio
    transcribed_text  TEXT,                             -- Whisper output
    answered_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 10. SCORES  -- evaluation output per answer (cosine similarity + rubric)
-- ============================================================================
CREATE TABLE scores (
    score_id          SERIAL PRIMARY KEY,
    answer_id         INTEGER UNIQUE NOT NULL REFERENCES answers(answer_id) ON DELETE CASCADE,
    similarity_score  NUMERIC(5,4),                     -- cosine similarity vs ideal_answer embedding
    relevance_score   NUMERIC(5,2),                      -- 0-100
    fluency_score     NUMERIC(5,2),                       -- 0-100 (from speech pacing / grammar)
    confidence_score  NUMERIC(5,2),                       -- 0-100
    final_score       NUMERIC(5,2),                        -- weighted aggregate
    evaluated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 11. FEEDBACK  -- Gemini-generated qualitative feedback per session
-- ============================================================================
CREATE TABLE feedback (
    feedback_id       SERIAL PRIMARY KEY,
    session_id        INTEGER UNIQUE NOT NULL REFERENCES interview_sessions(session_id) ON DELETE CASCADE,
    strengths         TEXT,
    areas_to_improve  TEXT,
    detailed_feedback TEXT,
    overall_rating    NUMERIC(3,1) CHECK (overall_rating BETWEEN 0 AND 10),
    generated_by      VARCHAR(20) DEFAULT 'gemini',
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 12. NOTIFICATIONS  -- system notifications for all user roles
-- ============================================================================
CREATE TABLE notifications (
    notification_id   SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title             VARCHAR(150) NOT NULL,
    message           TEXT NOT NULL,
    is_read           BOOLEAN DEFAULT FALSE,
    notification_type VARCHAR(30) DEFAULT 'info' CHECK (
                          notification_type IN ('info','success','warning','interview','application')
                      ),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES for query performance
-- ============================================================================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_jobs_recruiter ON jobs(recruiter_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_applications_candidate ON applications(candidate_id);
CREATE INDEX idx_applications_job ON applications(job_id);
CREATE INDEX idx_resumes_candidate ON resumes(candidate_id);
CREATE INDEX idx_questions_job ON interview_questions(job_id);
CREATE INDEX idx_sessions_candidate ON interview_sessions(candidate_id);
CREATE INDEX idx_answers_session ON answers(session_id);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);

-- ============================================================================
-- TRIGGER: auto-update users.updated_at on row change
-- ============================================================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- PHASE 2: Email OTP verification + password reset
-- ============================================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS email_otps (
    otp_id       SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    otp_hash     VARCHAR(255) NOT NULL,
    purpose      VARCHAR(30) NOT NULL CHECK (purpose IN ('email_verification','password_reset')),
    expires_at   TIMESTAMP NOT NULL,
    attempts     INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    used         BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_email_otps_user ON email_otps(user_id, purpose, used);

-- ============================================================================
-- PHASE 3: Recruiter approval workflow
-- ============================================================================
ALTER TABLE recruiters ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending'
    CHECK (status IN ('pending','approved','rejected','suspended'));
ALTER TABLE recruiters ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES users(user_id);
ALTER TABLE recruiters ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;

-- ============================================================================
-- PHASE 4: Resume versioning + ATS scoring
-- ============================================================================
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS version_number INTEGER DEFAULT 1;
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT TRUE;
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS extracted_name VARCHAR(150);
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS extracted_email VARCHAR(150);
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS extracted_phone VARCHAR(20);
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS ats_score NUMERIC(5,2);
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS ats_breakdown JSONB;

-- ============================================================================
-- PHASE 5: Aptitude test (30 MCQ)
-- ============================================================================
CREATE TABLE IF NOT EXISTS aptitude_questions (
    question_id   SERIAL PRIMARY KEY,
    category      VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    option_a      VARCHAR(255) NOT NULL,
    option_b      VARCHAR(255) NOT NULL,
    option_c      VARCHAR(255) NOT NULL,
    option_d      VARCHAR(255) NOT NULL,
    correct_option CHAR(1) NOT NULL CHECK (correct_option IN ('A','B','C','D')),
    difficulty    VARCHAR(20) DEFAULT 'medium'
);

CREATE TABLE IF NOT EXISTS aptitude_tests (
    test_id       SERIAL PRIMARY KEY,
    candidate_id  INTEGER NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    session_id    INTEGER REFERENCES interview_sessions(session_id) ON DELETE CASCADE,
    started_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at  TIMESTAMP,
    score         INTEGER,
    percentage    NUMERIC(5,2)
);

CREATE TABLE IF NOT EXISTS aptitude_test_questions (
    test_id       INTEGER NOT NULL REFERENCES aptitude_tests(test_id) ON DELETE CASCADE,
    question_id   INTEGER NOT NULL REFERENCES aptitude_questions(question_id),
    position      INTEGER NOT NULL,
    PRIMARY KEY (test_id, question_id)
);

CREATE TABLE IF NOT EXISTS aptitude_answers (
    answer_id     SERIAL PRIMARY KEY,
    test_id       INTEGER NOT NULL REFERENCES aptitude_tests(test_id) ON DELETE CASCADE,
    question_id   INTEGER NOT NULL REFERENCES aptitude_questions(question_id),
    selected_option CHAR(1),
    is_correct    BOOLEAN,
    UNIQUE(test_id, question_id)
);

-- ============================================================================
-- PHASE 6: Voice interview turn logging (for Realtime API sessions)
-- ============================================================================
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS mode VARCHAR(20) DEFAULT 'text'
    CHECK (mode IN ('text','audio_upload','realtime_voice'));
