"""
tests/test_jobs.py
--------------------
Tests for the Job posting, browsing, and Application modules.
Belongs in: backend/tests/test_jobs.py
"""

JOB_PAYLOAD = {
    "title": "Gen AI Engineer Intern",
    "description": "Work on LLM-based products and RAG pipelines.",
    "required_skills": ["Python", "LLM", "Prompt Engineering", "FastAPI"],
    "experience_level": "entry",
    "location": "Bengaluru",
    "job_type": "internship",
}


def test_recruiter_can_create_job(client, recruiter_token):
    response = client.post("/api/jobs", json=JOB_PAYLOAD, headers=recruiter_token)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == JOB_PAYLOAD["title"]
    assert body["status"] == "open"


def test_candidate_cannot_create_job(client, candidate_token):
    response = client.post("/api/jobs", json=JOB_PAYLOAD, headers=candidate_token)
    assert response.status_code == 403


def test_list_open_jobs(client, recruiter_token, candidate_token):
    client.post("/api/jobs", json=JOB_PAYLOAD, headers=recruiter_token)
    response = client.get("/api/jobs", headers=candidate_token)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_candidate_can_apply_to_job(client, recruiter_token, candidate_token):
    job_res = client.post("/api/jobs", json=JOB_PAYLOAD, headers=recruiter_token)
    job_id = job_res.json()["job_id"]

    apply_res = client.post("/api/applications", json={"job_id": job_id}, headers=candidate_token)
    assert apply_res.status_code == 201
    assert apply_res.json()["status"] == "applied"


def test_candidate_cannot_apply_twice(client, recruiter_token, candidate_token):
    job_res = client.post("/api/jobs", json=JOB_PAYLOAD, headers=recruiter_token)
    job_id = job_res.json()["job_id"]

    client.post("/api/applications", json={"job_id": job_id}, headers=candidate_token)
    second = client.post("/api/applications", json={"job_id": job_id}, headers=candidate_token)
    assert second.status_code == 400


def test_recruiter_can_view_applicants_for_own_job(client, recruiter_token, candidate_token):
    job_res = client.post("/api/jobs", json=JOB_PAYLOAD, headers=recruiter_token)
    job_id = job_res.json()["job_id"]
    client.post("/api/applications", json={"job_id": job_id}, headers=candidate_token)

    response = client.get(f"/api/applications/job/{job_id}", headers=recruiter_token)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_recruiter_can_update_application_status(client, recruiter_token, candidate_token):
    job_res = client.post("/api/jobs", json=JOB_PAYLOAD, headers=recruiter_token)
    job_id = job_res.json()["job_id"]
    apply_res = client.post("/api/applications", json={"job_id": job_id}, headers=candidate_token)
    application_id = apply_res.json()["application_id"]

    response = client.put(
        f"/api/applications/{application_id}/status", json={"status": "shortlisted"}, headers=recruiter_token
    )
    assert response.status_code == 200
    assert response.json()["status"] == "shortlisted"
