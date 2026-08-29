import logging
from typing import Dict, Any, List

from app.models.job import Job
from app.models.candidate import Candidate
from app.config import settings

logger = logging.getLogger(__name__)

# Fallback TF-IDF / Cosine Similarity helper
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

def normalize_skill(skill: str) -> str:
    return skill.strip().lower()

def match_skills(job_skills: List[str], candidate_skills: List[str]) -> tuple[List[str], List[str]]:
    """
    Compares job skills vs candidate extracted skills using case-insensitive & substring matching.
    Returns (matched_skills, missing_skills).
    """
    matched = []
    missing = []
    
    cand_skills_norm = [normalize_skill(s) for s in candidate_skills]
    
    for req_skill in job_skills:
        req_norm = normalize_skill(req_skill)
        # Direct match or substring match (e.g. 'rest api' in 'rest apis')
        is_found = False
        for c_skill in cand_skills_norm:
            if req_norm == c_skill or req_norm in c_skill or c_skill in req_norm:
                is_found = True
                break
        if is_found:
            matched.append(req_skill)
        else:
            missing.append(req_skill)
            
    return matched, missing

def calculate_vector_similarity(job_text: str, resume_text: str) -> float:
    """
    Calculates similarity score between job description and resume content (0.0 to 100.0).
    Uses scikit-learn TF-IDF vectorizer if available, or Jaccard token similarity fallback.
    """
    if not job_text.strip() or not resume_text.strip():
        return 50.0

    if HAS_SKLEARN:
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform([job_text, resume_text])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return round(float(sim) * 100.0, 2)
        except Exception as e:
            logger.warning(f"Error calculating TF-IDF similarity: {e}")
    
    # Simple Token Jaccard Fallback if sklearn is not installed
    set1 = set(job_text.lower().split())
    set2 = set(resume_text.lower().split())
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    if not union:
        return 50.0
    jaccard_sim = len(intersection) / len(union)
    return round(float(jaccard_sim * 100.0 * 2.5), 2)  # Normalized scale

def evaluate_candidate(candidate: Candidate, job: Job) -> Dict[str, Any]:
    """
    Evaluates candidate against job requirements and computes scores & recommendation verdict.
    """
    # 1. Match Required & Preferred Skills
    matched_req, missing_req = match_skills(job.required_skills or [], candidate.extracted_skills or [])
    matched_pref, missing_pref = match_skills(job.preferred_skills or [], candidate.extracted_skills or [])
    
    req_ratio = len(matched_req) / len(job.required_skills) if job.required_skills else 1.0
    pref_ratio = len(matched_pref) / len(job.preferred_skills) if job.preferred_skills else 1.0
    
    # Skills score out of 100
    if job.required_skills and job.preferred_skills:
        skills_score = (req_ratio * 75.0) + (pref_ratio * 25.0)
    elif job.required_skills:
        skills_score = req_ratio * 100.0
    else:
        skills_score = 100.0
        
    skills_score = round(skills_score, 2)
    
    # 2. Experience Score
    min_exp = job.min_experience_years or 0
    cand_exp = candidate.experience_years or 0.0
    
    if min_exp == 0:
        exp_score = 100.0
    elif cand_exp >= min_exp:
        # Bonus for extra experience up to 100% max cap
        exp_score = min(100.0, 85.0 + ((cand_exp - min_exp) * 5.0))
    else:
        # Partial credit
        exp_score = max(20.0, (cand_exp / min_exp) * 80.0)
        
    exp_score = round(exp_score, 2)
    
    # 3. Vector Text Similarity Score
    job_full_text = f"{job.title}\n{job.description}\n" + " ".join(job.required_skills or []) + " " + " ".join(job.preferred_skills or [])
    vector_score = calculate_vector_similarity(job_full_text, candidate.raw_text)
    
    # 4. Overall Weighted Score Calculation
    # Required skills match: 50%, Preferred: 20%, Exp: 15%, Vector Sim: 15%
    req_weighted = (req_ratio * 100.0) * 0.50
    pref_weighted = (pref_ratio * 100.0) * 0.20
    exp_weighted = exp_score * 0.15
    vec_weighted = vector_score * 0.15
    
    overall_score = round(req_weighted + pref_weighted + exp_weighted + vec_weighted, 2)
    overall_score = min(100.0, max(0.0, overall_score))
    
    # 5. Recommendation Verdict
    if overall_score >= 75.0 and len(missing_req) == 0:
        recommendation = "SHORTLIST"
    elif overall_score >= 65.0:
        recommendation = "SHORTLIST" if len(missing_req) <= 1 else "MAYBE"
    elif overall_score >= 50.0:
        recommendation = "MAYBE"
    else:
        recommendation = "REJECT"
        
    # 6. Generate Reasoning Explanation
    reasons = []
    if matched_req:
        reasons.append(f"Matched required skills: {', '.join(matched_req)}.")
    if missing_req:
        reasons.append(f"Missing required skills: {', '.join(missing_req)}.")
    if matched_pref:
        reasons.append(f"Matched preferred skills: {', '.join(matched_pref)}.")
    if missing_pref:
        reasons.append(f"Missing preferred skills: {', '.join(missing_pref)}.")
        
    if cand_exp >= min_exp:
        reasons.append(f"Experience level ({cand_exp} yrs) meets requirement ({min_exp} yrs).")
    else:
        reasons.append(f"Candidate experience ({cand_exp} yrs) is below requested ({min_exp} yrs).")
        
    reasoning_text = " ".join(reasons)
    
    # Optional LLM refinement if API key configured
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip() != "":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = f"""
Given the candidate screening summary for candidate '{candidate.name}' applying for '{job.title}':
Overall Score: {overall_score}%
Recommendation: {recommendation}
Matched Required: {matched_req}
Missing Required: {missing_req}
Matched Preferred: {matched_pref}
Missing Preferred: {missing_pref}

Provide a concise 2-sentence professional HR recommendation summary explaining the decision.
"""
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            reasoning_text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI reasoning generation failed, using standard template: {e}")

    return {
        "candidate_id": candidate.id,
        "job_id": job.id,
        "overall_score": overall_score,
        "skills_score": skills_score,
        "experience_score": exp_score,
        "vector_similarity_score": vector_score,
        "matched_required_skills": matched_req,
        "missing_required_skills": missing_req,
        "matched_preferred_skills": matched_pref,
        "missing_preferred_skills": missing_pref,
        "recommendation": recommendation,
        "reasoning": reasoning_text
    }
