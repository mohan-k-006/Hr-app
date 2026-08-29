# RecruitFlow - Resume Parser & Candidate Matcher

A backend service and HR dashboard built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Authlib (Google OAuth2)**, and **scikit-learn** to parse candidate resumes, extract tech skills and experience, and evaluate candidate alignment against job descriptions.

---

## Key Features

- **Google OAuth2 Authentication**: Sign in with Google integration using Authlib and Starlette session cookies.
- **Document Ingestion**: Extracts raw text from `.pdf`, `.docx`, and `.txt` resume files using PyMuPDF and python-docx.
- **Entity Extraction**: Normalizes contact details (Name, Email, Phone), education, tech skills taxonomy, and calculated years of experience.
- **Hybrid Matching Engine**:
  - Exact & substring skills taxonomy matching (Required vs Preferred breakdown).
  - Experience ratio scoring.
  - TF-IDF Cosine Similarity for semantic text alignment (`scikit-learn`).
  - Automated recommendation rules (`SHORTLIST`, `MAYBE`, `REJECT`) with natural language feedback.
- **HR Dashboard**: Web dashboard to post job requirements, multi-upload candidate resumes, view ranked leaderboards, select multiple resumes with checkboxes, and copy structured JSON evaluation outputs.
- **Postgres + SQLite Support**: Operates with PostgreSQL for production and includes SQLite fallback for local development.

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn
- **Authentication**: Authlib, Starlette SessionMiddleware (Google OAuth2)
- **Database**: PostgreSQL / SQLite, SQLAlchemy ORM
- **Document Parsing**: PyMuPDF (`fitz`), `python-docx`
- **Data & Matching**: `scikit-learn` (TF-IDF vectorizer), `pandas`, `pydantic`
- **Frontend**: Jinja2 Templates, HTML5, Vanilla CSS, JavaScript (Fetch API)
- **Testing**: `pytest`, `httpx`

---

## Google OAuth2 Setup

1. Create OAuth credentials in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Set Authorized redirect URI to: `http://127.0.0.1:8000/api/auth/google/callback`
3. Add credentials to your `.env` file:
   ```env
   GOOGLE_CLIENT_ID="your-google-client-id"
   GOOGLE_CLIENT_SECRET="your-google-client-secret"
   SECRET_KEY="your-session-secret-key"
   ```

---

## Project Structure

```text
ai-resume-screener/
├── app/
│   ├── main.py            # FastAPI entrypoint, middlewares & routes
│   ├── config.py          # App configuration & environment settings
│   ├── database.py        # SQLAlchemy engine & session management
│   ├── models/            # SQLAlchemy DB entities (Job, Candidate, ScreeningResult)
│   ├── schemas/           # Pydantic validation schemas
│   ├── services/
│   │   ├── parser.py      # PDF & DOCX text extraction
│   │   ├── extractor.py   # Regex & taxonomy entity extraction
│   │   └── matcher.py     # Skill breakdown & TF-IDF match algorithm
│   ├── api/
│   │   ├── jobs.py        # Job requirements REST endpoints
│   │   ├── candidates.py  # Resume upload & candidate management
│   │   ├── screening.py   # AI screening execution & leaderboards
│   │   └── auth.py        # Google OAuth2 login & session routes
│   ├── static/            # Dashboard CSS & JavaScript
│   └── templates/         # HTML Jinja templates
├── sample_resumes/        # Test resume samples
├── tests/                 # Unit and integration test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file (or copy `.env.example`):

```bash
DATABASE_URL=sqlite:///./resume_screener.db
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload
```

Access the app at:
- **Dashboard**: `http://127.0.0.1:8000`
- **API Documentation (Swagger)**: `http://127.0.0.1:8000/docs`

---

## Running Tests

Execute the unit and integration test suite:

```bash
pytest -v
```

---

## Docker Deployment

To run the complete stack with PostgreSQL using Docker Compose:

```bash
docker-compose up --build
```
