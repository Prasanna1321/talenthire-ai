"""
tests/test_recruiter_approval.py
------------------------------------
Phase 3: recruiter approval workflow — specifically verifies the BACKEND
enforcement (a pending recruiter's token must be rejected by the API
directly), not just that the frontend hides a button.
Belongs in: backend/tests/test_recruiter_approval.py
"""

JOB_PAYLOAD = {
    "title": "Gen AI Engineer Intern",
    "description": "Work on LLM-based products.",
    "required_skills": ["Python", "LLM"],
    "experience_level": "entry",
    "location": "Bengaluru",
    "job_type": "internship",
}


def test_pending_recruiter_cannot_create_job(client, pending_recruiter_token):
    response = client.post("/api/jobs", json=JOB_PAYLOAD, headers=pending_recruiter_token)
    assert response.status_code == 403
    assert "pending" in response.json()["detail"].lower()


def test_pending_recruiter_can_still_login_and_view_profile(client, pending_recruiter_token):
    """Pending status blocks job management specifically, not login/profile access."""
    response = client.get("/api/users/recruiter/profile", headers=pending_recruiter_token)
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_admin_can_approve_recruiter_and_then_job_creation_succeeds(client, pending_recruiter_token, admin_token):
    profile_resp = client.get("/api/users/recruiter/profile", headers=pending_recruiter_token)
    recruiter_id = profile_resp.json()["recruiter_id"]

    approve_resp = client.post(f"/api/admin/recruiters/{recruiter_id}/approve", headers=admin_token)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    job_resp = client.post("/api/jobs", json=JOB_PAYLOAD, headers=pending_recruiter_token)
    assert job_resp.status_code == 201


def test_non_admin_cannot_approve_recruiters(client, candidate_token, pending_recruiter_token):
    profile_resp = client.get("/api/users/recruiter/profile", headers=pending_recruiter_token)
    recruiter_id = profile_resp.json()["recruiter_id"]

    response = client.post(f"/api/admin/recruiters/{recruiter_id}/approve", headers=candidate_token)
    assert response.status_code == 403
