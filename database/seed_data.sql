-- ============================================================================
-- TalentHire AI - Seed Data (for local development / demo)
-- Run AFTER schema.sql
-- Passwords below are bcrypt hashes of the plaintext "Password123!"
-- ============================================================================

-- Admin
INSERT INTO users (full_name, email, password_hash, role) VALUES
('System Admin', 'admin@talenthire.ai', '$2b$12$KIXQyU1YV8N1Z3H8n8Q1qO1FZ8v9y7QpN5t1cQ9m8Q1Z3H8n8Q1qO', 'admin');

-- Recruiter user + profile
INSERT INTO users (full_name, email, password_hash, role) VALUES
('Ananya Rao', 'ananya.rao@techcorp.com', '$2b$12$KIXQyU1YV8N1Z3H8n8Q1qO1FZ8v9y7QpN5t1cQ9m8Q1Z3H8n8Q1qO', 'recruiter');
INSERT INTO recruiters (user_id, company_name, designation, company_website) VALUES
((SELECT user_id FROM users WHERE email = 'ananya.rao@techcorp.com'), 'TechCorp Solutions', 'Senior HR Manager', 'https://techcorp.example.com');

-- Candidate user + profile
INSERT INTO users (full_name, email, password_hash, role) VALUES
('Praveen Kumar', 'praveen.kumar@example.com', '$2b$12$KIXQyU1YV8N1Z3H8n8Q1qO1FZ8v9y7QpN5t1cQ9m8Q1Z3H8n8Q1qO', 'candidate');
INSERT INTO candidates (user_id, phone, location, highest_education, years_experience, linkedin_url, github_url) VALUES
((SELECT user_id FROM users WHERE email = 'praveen.kumar@example.com'), '+91-9876543210', 'Shivamogga, Karnataka', 'B.E. Computer Science', 0, 'https://linkedin.com/in/example', 'https://github.com/example');

-- Job posting
INSERT INTO jobs (recruiter_id, title, description, required_skills, experience_level, location, job_type)
VALUES (
    (SELECT recruiter_id FROM recruiters LIMIT 1),
    'Gen AI Engineer Intern',
    'Work on LLM-based products, RAG pipelines, and prompt engineering for enterprise clients.',
    ARRAY['Python','Machine Learning','LLM','Prompt Engineering','FastAPI'],
    'entry',
    'Bengaluru, India',
    'internship'
);

-- Interview questions for that job
INSERT INTO interview_questions (job_id, question_text, question_type, difficulty, ideal_answer, generated_by)
VALUES
((SELECT job_id FROM jobs LIMIT 1),
 'Explain the difference between supervised and unsupervised learning with examples.',
 'technical', 'easy',
 'Supervised learning uses labeled data to train models (e.g. classification, regression) while unsupervised learning finds patterns in unlabeled data (e.g. clustering, dimensionality reduction).',
 'gemini'),
((SELECT job_id FROM jobs LIMIT 1),
 'What is Retrieval-Augmented Generation (RAG) and why is it used with LLMs?',
 'technical', 'medium',
 'RAG combines a retrieval system with a generative LLM: relevant documents are fetched from a knowledge base and passed as context to the LLM, reducing hallucination and grounding answers in real data.',
 'gemini'),
((SELECT job_id FROM jobs LIMIT 1),
 'Describe a challenging technical problem you solved and how you approached it.',
 'behavioral', 'medium',
 NULL,
 'gemini');
