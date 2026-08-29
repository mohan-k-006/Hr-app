import pytest
from app.services.matcher import match_skills, calculate_vector_similarity, evaluate_candidate
from app.models.job import Job
from app.models.candidate import Candidate

def test_match_skills():
    req_skills = ["Python", "FastAPI", "REST APIs", "PostgreSQL", "Git"]
    cand_skills = ["Python", "REST APIs", "PostgreSQL", "Git", "Docker"]
    
    matched, missing = match_skills(req_skills, cand_skills)
    assert "Python" in matched
    assert "REST APIs" in matched
    assert "PostgreSQL" in matched
    assert "Git" in matched
    assert "FastAPI" in missing

def test_calculate_vector_similarity():
    text1 = "Python developer experienced in building web applications and REST APIs using FastAPI."
    text2 = "Senior Python engineer specialized in backend REST API design and web services."
    
    sim = calculate_vector_similarity(text1, text2)
    assert sim > 10.0

def test_evaluate_candidate():
    job = Job(
        id=1,
        title="Python Developer",
        description="Python backend developer required",
        required_skills=["Python", "FastAPI", "REST APIs", "PostgreSQL", "Git"],
        preferred_skills=["Docker", "AWS"],
        min_experience_years=2
    )
    
    candidate = Candidate(
        id=1,
        name="Rahul Kumar",
        filename="rahul.txt",
        file_type="txt",
        raw_text="Rahul Kumar. Python, REST APIs, PostgreSQL, Git, Docker. 3 years experience.",
        extracted_skills=["Python", "REST APIs", "PostgreSQL", "Git", "Docker"],
        experience_years=3.0
    )
    
    eval_result = evaluate_candidate(candidate, job)
    
    assert eval_result["candidate_id"] == 1
    assert eval_result["job_id"] == 1
    assert eval_result["recommendation"] in ["SHORTLIST", "MAYBE"]
    assert "Python" in eval_result["matched_required_skills"]
    assert "FastAPI" in eval_result["missing_required_skills"]
    assert "Docker" in eval_result["matched_preferred_skills"]
    assert "AWS" in eval_result["missing_preferred_skills"]
