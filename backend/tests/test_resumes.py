"""
tests/test_resumes.py
------------------------
Tests for the Resume Upload / Parser / Classification / Phase 4 versioning
+ ATS scoring modules. Belongs in: backend/tests/test_resumes.py

The actual ML pipeline (PyMuPDF/spaCy/SkillNER/sentence-transformers/
RandomForest) is mocked here so these tests run fast and don't require
the multi-GB ML dependencies to be installed just to validate the API
contract, auth rules, and DB writes.
"""

import io
from unittest.mock import patch

from app.models.resume import Resume


def _fake_process_resume(db, candidate_id, upload, force=False):
    """Mirrors the real process_resume()'s dict return shape (Phase 4)."""
    resume = Resume(
        candidate_id=candidate_id,
        file_path="uploads/resumes/fake.pdf",
        original_filename=upload.filename,
        raw_text="Experienced Python developer skilled in FastAPI and machine learning.",
        extracted_skills=["python", "fastapi", "machine learning"],
        predicted_category="Generative AI / LLM Engineering",
        prediction_confidence=0.92,
        embedding=[0.1, 0.2, 0.3],
        version_number=1,
        is_current=True,
        extracted_name="Test Candidate",
        extracted_email="candidate@test.com",
        extracted_phone="1234567890",
        ats_score=72.5,
        ats_breakdown={"skills_match": 25.0, "experience": 15.0, "education": 8.0, "projects": 12.0, "keywords": 5.0, "completeness": 5.0, "formatting": 2.5},
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return {"requires_confirmation": False, "resume": resume}


def test_upload_resume_rejects_non_pdf(client, candidate_token):
    fake_file = io.BytesIO(b"not a real pdf")
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.txt", fake_file, "text/plain")},
        headers=candidate_token,
    )
    assert response.status_code == 400


@patch("app.routers.resumes.process_resume", side_effect=_fake_process_resume)
def test_upload_resume_success(mock_process, client, candidate_token):
    fake_file = io.BytesIO(b"%PDF-1.4 fake pdf content")
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.pdf", fake_file, "application/pdf")},
        headers=candidate_token,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["requires_confirmation"] is False
    assert body["resume"]["ats_score"] == 72.5
    assert "python" in body["resume"]["extracted_skills"]
    # PHASE 4: classification is no longer exposed on the resume response at all
    assert "predicted_category" not in body["resume"]


def test_upload_resume_requires_auth(client):
    fake_file = io.BytesIO(b"%PDF-1.4 fake pdf content")
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.pdf", fake_file, "application/pdf")},
    )
    assert response.status_code == 401


@patch("app.routers.resumes.process_resume", side_effect=_fake_process_resume)
def test_list_my_resumes(mock_process, client, candidate_token):
    fake_file = io.BytesIO(b"%PDF-1.4 fake pdf content")
    client.post(
        "/api/resumes/upload",
        files={"file": ("resume.pdf", fake_file, "application/pdf")},
        headers=candidate_token,
    )
    response = client.get("/api/resumes/mine", headers=candidate_token)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["version_number"] == 1
