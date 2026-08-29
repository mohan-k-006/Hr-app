import re
import json
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

# Common Tech & Professional Skill Taxonomy for fast matching
COMMON_SKILLS_TAXONOMY = [
    "python", "fastapi", "django", "flask", "postgresql", "postgres", "sqlite", "mysql", "mongodb",
    "git", "github", "docker", "kubernetes", "aws", "azure", "gcp", "rest api", "rest apis", "restful api",
    "graphql", "html", "css", "javascript", "typescript", "react", "next.js", "angular", "vue", "node.js",
    "express", "java", "spring boot", "c++", "c#", ".net", "golang", "go", "rust", "php", "laravel",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", "opencv", "nltk", "spacy",
    "llm", "openai", "langchain", "prompt engineering", "redis", "rabbitmq", "kafka", "elasticsearch",
    "ci/cd", "jenkins", "github actions", "linux", "bash", "unit testing", "pytest", "postman",
    "agile", "jira", "scrum", "data structure", "algorithms", "system design", "microservices"
]

EDUCATION_KEYWORDS = [
    "b.tech", "btech", "b.e", "be", "m.tech", "mtech", "m.e", "m.sc", "b.sc", "bca", "mca",
    "bachelor of technology", "bachelor of engineering", "bachelor of science", "master of computer applications",
    "master of technology", "master of science", "ph.d", "phd", "bachelor", "master", "degree"
]

GENERIC_WORDS = {"resume", "cv", "curriculum", "vitae", "profile", "bio", "biodata", "summary", "contact", "application", "document", "v1", "v2", "final", "draft"}

def extract_email(text: str) -> str | None:
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None

def extract_phone(text: str) -> str | None:
    match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    return match.group(0) if match else None

def extract_candidate_name(text: str, filename: str) -> str:
    # 1. Clean filename to derive candidate name fallback
    base_filename = filename.rsplit('.', 1)[0]
    clean_fn = re.sub(r'[\-_()0-9]', ' ', base_filename)
    fn_words = [w for w in clean_fn.split() if w.lower() not in GENERIC_WORDS]
    filename_derived_name = " ".join(fn_words).title() if fn_words else ""

    # 2. Extract candidate name from top lines of text
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text_derived_name = ""
    if lines:
        for line in lines[:5]:
            clean_line = line.strip()
            # Skip emails, phones, URLs
            if re.search(r'[@\d:]|http|www', clean_line):
                continue
            words = clean_line.split()
            # Skip if any word is a generic section header
            if any(w.lower() in GENERIC_WORDS for w in words):
                continue
            if 1 <= len(words) <= 4 and all(re.match(r'^[A-Za-z.\'-]+$', w) for w in words):
                text_derived_name = clean_line.title()
                break

    # Prioritize extracted text name if valid and not generic
    if text_derived_name and text_derived_name.lower() not in GENERIC_WORDS:
        return text_derived_name

    # Otherwise use filename derived name if available
    if filename_derived_name:
        return filename_derived_name

    return "Candidate"

def extract_skills_regex(text: str) -> List[str]:
    text_lower = text.lower()
    found_skills = set()
    
    for skill in COMMON_SKILLS_TAXONOMY:
        # Match as whole word / token
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            # Normalize display capitalization
            if skill in ["rest api", "rest apis", "restful api"]:
                found_skills.add("REST APIs")
            elif skill in ["postgresql", "postgres"]:
                found_skills.add("PostgreSQL")
            elif skill in ["fastapi"]:
                found_skills.add("FastAPI")
            elif skill in ["python"]:
                found_skills.add("Python")
            elif skill in ["git"]:
                found_skills.add("Git")
            elif skill in ["docker"]:
                found_skills.add("Docker")
            elif skill in ["aws"]:
                found_skills.add("AWS")
            elif skill in ["pytest"]:
                found_skills.add("pytest")
            else:
                found_skills.add(skill.title() if len(skill) > 3 else skill.upper())
                
    return sorted(list(found_skills))

def extract_education(text: str) -> List[str]:
    text_lower = text.lower()
    found = set()
    for kw in EDUCATION_KEYWORDS:
        if kw in text_lower:
            found.add(kw.upper() if len(kw) <= 5 else kw.title())
    return sorted(list(found))

def extract_experience_years(text: str) -> float:
    # Pattern 1: "3+ years", "4 years of experience", "2.5 years"
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?', text, re.IGNORECASE)
    if matches:
        years = [float(m) for m in matches if float(m) < 40]
        if years:
            return max(years)
    
    # Pattern 2: Year range calculation e.g. "2020 - 2024"
    year_ranges = re.findall(r'\b(20\d{2})\s*[-–to]+\s*(20\d{2}|present|current)\b', text, re.IGNORECASE)
    if year_ranges:
        total_yrs = 0.0
        current_yr = 2026
        for start, end in year_ranges:
            start_yr = int(start)
            end_yr = current_yr if end.lower() in ["present", "current"] else int(end)
            diff = max(0, end_yr - start_yr)
            total_yrs += diff
        if total_yrs > 0:
            return min(total_yrs, 40.0)
            
    return 1.0  # Default baseline for fresher/parsed resume

def extract_candidate_info(raw_text: str, filename: str) -> Dict[str, Any]:
    """
    Main extraction pipeline.
    Uses regex rule-based extraction by default. If OPENAI_API_KEY is configured,
    enhances output using OpenAI LLM.
    """
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    name = extract_candidate_name(raw_text, filename)
    skills = extract_skills_regex(raw_text)
    education = extract_education(raw_text)
    exp_years = extract_experience_years(raw_text)

    parsed = {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "education": education,
        "experience_years": exp_years
    }

    # Optional OpenAI LLM enhancement if key is provided
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip() != "":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = f"""
Extract candidate information from the following resume text. Return valid JSON only with keys:
"name" (str), "email" (str), "phone" (str), "skills" (list of str), "education" (list of str), "experience_years" (float).

Resume text:
{raw_text[:3000]}
"""
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            llm_result = json.loads(response.choices[0].message.content)
            
            if llm_result.get("name"): parsed["name"] = llm_result["name"]
            if llm_result.get("email"): parsed["email"] = llm_result["email"]
            if llm_result.get("phone"): parsed["phone"] = llm_result["phone"]
            if llm_result.get("skills"):
                # merge skills
                combined = set(parsed["skills"] + llm_result["skills"])
                parsed["skills"] = sorted(list(combined))
            if llm_result.get("education"):
                parsed["education"] = llm_result["education"]
            if llm_result.get("experience_years") is not None:
                parsed["experience_years"] = float(llm_result["experience_years"])
        except Exception as e:
            logger.warning(f"OpenAI extraction call failed, using rule-based extraction: {e}")

    return parsed
