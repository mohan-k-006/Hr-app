import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "sqlite:///./test_resume_screener.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_resume_screener.db"):
        try:
            os.remove("test_resume_screener.db")
        except Exception:
            pass

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_job_and_screening_flow():
    # 1. Create Job
    job_payload = {
        "title": "Python Backend Engineer",
        "department": "Engineering",
        "description": "FastAPI and PostgreSQL backend developer needed.",
        "required_skills": ["Python", "FastAPI", "REST APIs", "PostgreSQL", "Git"],
        "preferred_skills": ["Docker", "AWS"],
        "min_experience_years": 2
    }
    job_res = client.post("/api/jobs/", json=job_payload)
    assert job_res.status_code == 201
    job_data = job_res.json()
    job_id = job_data["id"]

    # 2. Upload Candidate Resume
    resume_content = b"Rahul Kumar\nEmail: rahul@example.com\nSkills: Python, REST APIs, PostgreSQL, Git, Docker.\nExperience: 3 years"
    files = [("files", ("rahul_kumar.txt", resume_content, "text/plain"))]
    
    upload_res = client.post("/api/candidates/upload", files=files)
    assert upload_res.status_code == 201
    candidates = upload_res.json()
    assert len(candidates) == 1
    cand_id = candidates[0]["id"]

    # 3. Trigger Screening
    screen_res = client.post(f"/api/screening/screen/{job_id}/{cand_id}")
    assert screen_res.status_code == 200
    screen_data = screen_res.json()

    assert screen_data["job_id"] == job_id
    assert screen_data["candidate_id"] == cand_id
    assert screen_data["overall_score"] > 50.0
    assert "Python" in screen_data["matched_required_skills"]
    assert "FastAPI" in screen_data["missing_required_skills"]
