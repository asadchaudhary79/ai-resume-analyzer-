# 🚀 AI-Powered Resume Analyzer — Development Plan

> **Project:** AI-Powered Resume Analyzer API  
> **Tech Stack:** FastAPI + OpenAI GPT-4o + PyPDF2 + Celery + PostgreSQL + Redis + Docker  
> **Access:** Public API (No Authentication Required)  
> **Estimated Duration:** ~2 Weeks  
> **Difficulty:** Intermediate–Advanced

---

## 📌 Project Overview

A production-grade REST API that allows users to upload their resume (PDF/DOCX), get an AI-powered score, receive improvement suggestions, and match their resume against any job description — all powered by OpenAI GPT-4o with async background processing via Celery.

---

## 🗂️ Folder Structure

```
resume-analyzer/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── api/
│   │   └── routes/
│   │       ├── resume.py
│   │       └── analysis.py
│   ├── models/
│   │   ├── resume.py
│   │   └── analysis.py
│   ├── schemas/
│   │   ├── resume.py
│   │   └── analysis.py
│   ├── services/
│   │   ├── pdf_parser.py
│   │   ├── ai_analyzer.py
│   │   ├── job_matcher.py
│   │   └── scorer.py
│   ├── tasks/
│   │   └── celery_tasks.py
│   └── utils/
│       ├── file_handler.py    # Local file save/delete logic
│       └── helpers.py
├── uploads/                   # 📁 Local file storage directory
│   └── .gitkeep
├── tests/
│   ├── test_upload.py
│   ├── test_analysis.py
│   ├── test_matching.py
│   └── conftest.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Tech Stack

| Technology                    | Purpose                        |
| ----------------------------- | ------------------------------ |
| FastAPI                       | Main API framework             |
| PostgreSQL                    | Primary database               |
| SQLAlchemy + Alembic          | ORM + Migrations               |
| PyPDF2 / pdfplumber           | PDF text extraction            |
| OpenAI GPT-4o                 | AI analysis engine             |
| Celery                        | Background task processing     |
| Redis                         | Celery broker + caching        |
| Local Filesystem (`/uploads`) | File storage (no cloud needed) |
| Docker + Docker Compose       | Containerization               |

---

## 📊 Phase Implementation Status

| Phase | Status      | Notes |
| ----- | ----------- | ----- |
| **1** | ✅ Complete | FastAPI app, config, DB, CORS, health, Swagger, uploads dir, Alembic, Docker Compose |
| **2** | ✅ Complete | Resume upload, PDF/DOCX parsing, file handler, CRUD endpoints |
| **3** | ✅ Complete | OpenAI integration, scoring, analysis endpoints, Redis cache |
| **4** | ✅ Complete | Job description matching, match history |
| **5** | ✅ Complete | Celery worker, async analysis, Flower, cleanup task |
| **6** | ✅ Complete | Dashboard stats, improvement trend |
| **7** | ✅ Complete | Docker (Celery + Flower), tests, rate limiting (SlowAPI), README, OpenAPI/Postman |

---

## 📅 Development Timeline

### Phase 1 — Project Setup & Base Configuration ✅

**Duration: 1–2 Days**

**Tasks:**

- Initialize FastAPI project structure
- Configure PostgreSQL + SQLAlchemy + Alembic
- Set up `.env` configuration with `pydantic-settings`
- Create `uploads/` directory with auto-create logic on startup
- Add CORS middleware (allow all origins — public access)
- Add global exception handlers
- Configure Swagger UI with proper tags and descriptions
- Write base health check endpoint

**API Endpoints:**

```
GET /api/v1/health       # Health check — server status
GET /api/v1/docs         # Swagger UI (auto-generated)
```

**Deliverable:** Running FastAPI server with DB connection and public access ✅

---

### Phase 2 — Resume Upload & PDF Parsing ✅

**Duration: 2–3 Days**

**Tasks:**

- Build public file upload endpoint (no auth required)
- Validate file type (PDF/DOCX only) and size (max 5MB)
- Save uploaded file to local `uploads/` directory with UUID filename
- Store file path in PostgreSQL (not S3 URL)
- Use PyPDF2 / pdfplumber to extract raw text
- Parse structured fields: name, email, phone, skills, experience, education, projects
- Save parsed data as JSONB in PostgreSQL
- Handle edge cases: scanned PDFs, multi-page, bad formatting

**Local File Handler Logic:**

```python
# utils/file_handler.py
import uuid, shutil
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def save_file(file) -> str:
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return str(file_path)   # Store this path in DB

def delete_file(file_path: str):
    Path(file_path).unlink(missing_ok=True)
```

**API Endpoints:**

```
POST   /api/v1/resumes/upload       # Upload PDF/DOCX — public
GET    /api/v1/resumes/             # List all resumes
GET    /api/v1/resumes/{resume_id}  # Get single resume details
DELETE /api/v1/resumes/{resume_id}  # Delete resume + local file
```

**Extracted Data Format:**

```json
{
  "name": "Ali Hassan",
  "email": "ali@gmail.com",
  "phone": "+92-xxx",
  "skills": ["Python", "FastAPI", "Docker"],
  "experience": [...],
  "education": [...],
  "projects": [...],
  "certifications": [...]
}
```

**Deliverable:** Public resume upload with local storage + JSON extraction ✅

---

### Phase 3 — AI Analysis Engine ✅

**Duration: 3–4 Days**

**Tasks:**

- Integrate OpenAI GPT-4o API
- Design smart system prompt for resume analysis
- Parse and validate AI JSON response
- Build scoring logic (0–100 overall + per-section)
- Return strengths, weaknesses, suggestions, missing ATS keywords
- Estimate experience level (junior/mid/senior)
- Add response caching with Redis (avoid duplicate API calls)

**API Endpoints:**

```
POST /api/v1/analysis/analyze/{resume_id}
GET  /api/v1/analysis/{analysis_id}
GET  /api/v1/analysis/history
```

**AI Prompt Strategy:**

```python
system_prompt = """
You are an expert HR consultant and ATS system.
Analyze the resume and return a strict JSON object with:
- overall_score (0-100)
- section_scores: { experience, skills, education, formatting }
- strengths (list of strings)
- weaknesses (list of strings)
- suggestions (list of actionable improvements)
- ats_keywords_missing (list)
- estimated_experience_level (junior | mid | senior)
"""
```

**Sample AI Output:**

```json
{
  "overall_score": 72,
  "section_scores": {
    "experience": 80,
    "skills": 70,
    "education": 75,
    "formatting": 65
  },
  "strengths": ["Strong Python skills", "Good project variety"],
  "weaknesses": ["No quantified achievements", "Missing LinkedIn"],
  "suggestions": [
    "Add metrics to experience (e.g. improved speed by 40%)",
    "Include GitHub profile link"
  ],
  "ats_keywords_missing": ["REST API", "CI/CD", "Microservices"],
  "experience_level": "junior"
}
```

**Deliverable:** Full AI analysis with scoring and suggestions ✅

---

### Phase 4 — Job Description Matching ✅

**Duration: 2 Days**

**Tasks:**

- Accept job description as input text
- Use GPT-4o to compare resume vs JD
- Return match score, matched/missing keywords, recommendation
- Store match history in DB

**API Endpoints:**

```
POST /api/v1/analysis/match-job
GET  /api/v1/analysis/match-history
```

**Request Body:**

```json
{
  "resume_id": "uuid-here",
  "job_description": "We are looking for a Python developer with FastAPI, Docker, and AWS experience..."
}
```

**Match Response:**

```json
{
  "match_score": 68,
  "matched_keywords": ["Python", "FastAPI", "PostgreSQL"],
  "missing_keywords": ["Kubernetes", "AWS", "GraphQL"],
  "recommendation": "You match 68% of this job. Add cloud skills to improve chances.",
  "should_apply": true
}
```

**Deliverable:** Job description matching with keyword analysis ✅

---

### Phase 5 — Celery Background Tasks ✅

**Duration: 2 Days**

**Tasks:**

- Set up Celery with Redis as broker
- Move heavy AI processing to background tasks
- Implement email notification on analysis complete
- Add PDF report generation task
- Add scheduled cleanup task (delete 30-day-old files)
- Set up Flower dashboard for task monitoring

**Task Flow:**

```
User uploads resume
        ↓
API returns task_id instantly (202 Accepted)
        ↓
Celery worker processes AI analysis in background
        ↓
Result saved to DB
        ↓
User polls GET /analysis/{task_id} for result
```

**Tasks Defined:**

```python
@celery.task
def analyze_resume_async(resume_id): ...

@celery.task
def generate_pdf_report(analysis_id): ...

@celery.task
def cleanup_old_files(): ...  # Runs on schedule — deletes old local files
```

**Deliverable:** Non-blocking async analysis with background processing ✅

---

### Phase 6 — Dashboard & Analytics ✅

**Duration: 1–2 Days**

**Tasks:**

- Build user dashboard stats endpoint
- Track score improvement over time
- Show total resumes, analyses, job matches

**API Endpoints:**

```
GET /api/v1/dashboard/stats
GET /api/v1/dashboard/improvement-trend
```

**Response:**

```json
{
  "total_resumes": 5,
  "average_score": 71,
  "best_score": 85,
  "total_job_matches": 12,
  "improvement_over_time": [65, 68, 71, 75, 85]
}
```

**Deliverable:** User analytics and progress tracking ✅

---

### Phase 7 — Docker, Testing & Documentation ✅

**Duration: 2–3 Days**

**Tasks:**

- Write Dockerfile and docker-compose.yml (API + DB + Redis + Celery + Flower)
- Write unit and integration tests (pytest + httpx)
- Add global rate limiting (slowapi) — e.g. 20 requests/minute per IP
- Add `uploads/` volume mount in Docker so files persist
- Polish Swagger/OpenAPI auto-docs
- Write comprehensive README.md with GIF demo, architecture diagram, setup guide
- Create Postman collection
- Add `.env.example` file

**docker-compose.yml Services:**

```yaml
services:
  api: # FastAPI application
  db: # PostgreSQL database
  redis: # Celery broker + cache
  celery: # Background worker
  flower: # Celery monitoring UI

volumes:
  uploads_data: # Persist local uploaded files
  postgres_data: # Persist database
```

**Deliverable:** Fully dockerized, tested, documented project ✅

---

## 🗄️ Database Schema

```
Resumes
├── id (UUID), filename, local_path     # local_path = "uploads/uuid_filename.pdf"
├── parsed_text (TEXT), parsed_data (JSONB), uploaded_at

Analyses
├── id (UUID), resume_id (FK), overall_score (INT)
├── section_scores (JSONB), strengths (JSONB)
├── weaknesses (JSONB), suggestions (JSONB)
├── status (pending | done | failed), created_at

JobMatches
├── id (UUID), resume_id (FK), job_description (TEXT)
├── match_score (INT), matched_keywords (JSONB)
├── missing_keywords (JSONB), created_at
```

---

## 🌟 Bonus Features (Optional Add-ons)

| Feature                | Description                               |
| ---------------------- | ----------------------------------------- |
| IP-based Rate Limiting | 20 requests/min per IP (slowapi)          |
| Resume Comparison      | Compare 2 resume versions side-by-side    |
| Multi-language Support | Handle English + Urdu resumes             |
| Webhook Support        | Notify external URL when analysis is done |
| Resume Scoring History | Track improvement over multiple uploads   |

---

## 📋 GitHub README Checklist

- [ ] Project description and live demo GIF
- [ ] Architecture diagram (draw.io or Excalidraw)
- [ ] API documentation link (Swagger UI)
- [ ] Docker setup instructions
- [ ] `.env.example` file with all required variables
- [ ] Postman collection download link
- [ ] Test coverage badge
- [ ] Tech stack badges (FastAPI, Python, PostgreSQL, Redis, Docker)

---

## ✅ Final Summary

| Phase     | Task                              | Duration     | Status      |
| --------- | --------------------------------- | ------------ | ----------- |
| 1         | Project Setup + Base Config       | 1–2 days     | ✅ Complete |
| 2         | File Upload (Local) + PDF Parsing | 2–3 days     | ✅ Complete |
| 3         | AI Analysis Engine                | 3–4 days     | ✅ Complete |
| 4         | Job Description Matching          | 2 days       | ✅ Complete |
| 5         | Celery Background Tasks           | 2 days       | ✅ Complete |
| 6         | Dashboard + Stats                 | 1–2 days     | ✅ Complete |
| 7         | Docker + Testing + Docs           | 2–3 days     | ✅ Complete |
| **Total** |                                   | **~2 Weeks** | 7/7 done    |

---

> 💡 **Pro Tip:** Start with Phase 1–2 without AI first. Test file upload and local storage fully. Then layer in AI in Phase 3. This way you avoid wasting OpenAI API credits during development.
