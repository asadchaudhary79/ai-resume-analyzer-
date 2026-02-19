# AI-Powered Resume Analyzer API

REST API for resume upload (PDF/DOCX), AI-powered analysis and scoring, job description matching, and dashboard analytics. Built with **FastAPI**, **OpenAI GPT-4o**, **PostgreSQL**, **Redis**, **Celery**, and **Docker**.

## Features

- **Resume upload** — PDF/DOCX, max 5MB, stored locally; text and structured data extracted
- **AI analysis** — Overall and section scores, strengths/weaknesses, suggestions, ATS keywords, experience level
- **Job matching** — Compare resume to any job description; match score, keywords, recommendation
- **Background processing** — Optional Celery tasks for async analysis and scheduled cleanup
- **Dashboard API** — Stats (total resumes, average/best score, job matches) and improvement trend
- **Rate limiting** — 20 requests/minute per IP (configurable)

## Quick start (Docker)

1. **Clone and set env**
   ```bash
   cp .env.example .env
   ```
   Add `OPENAI_API_KEY` to `.env` for full AI analysis and job matching (optional; mock responses otherwise).

2. **Run all services**
   ```bash
   docker compose up -d
   ```

3. **Open**
   - **API root:** http://localhost:8000  
   - **Swagger UI:** http://localhost:8000/api/v1/docs  
   - **Health:** http://localhost:8000/api/v1/health  

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/docs` | Swagger UI |
| POST | `/api/v1/resumes/upload` | Upload PDF/DOCX resume |
| GET | `/api/v1/resumes/` | List resumes |
| GET | `/api/v1/resumes/{id}` | Get resume |
| DELETE | `/api/v1/resumes/{id}` | Delete resume |
| POST | `/api/v1/analysis/analyze/{resume_id}` | Analyze resume (sync) |
| POST | `/api/v1/analysis/analyze/{resume_id}?background=true` | Analyze in background (202) |
| GET | `/api/v1/analysis/{analysis_id}` | Get analysis result |
| GET | `/api/v1/analysis/history` | Analysis history |
| POST | `/api/v1/analysis/match-job` | Match resume to job description |
| GET | `/api/v1/analysis/match-history` | Match history |
| GET | `/api/v1/dashboard/stats` | Dashboard stats |
| GET | `/api/v1/dashboard/improvement-trend` | Score trend over time |

**Postman:** Import from `GET http://localhost:8000/api/v1/openapi.json`.

## Run locally (no Docker)

- Python 3.12+, PostgreSQL, Redis
- Create DB: `createdb resume_analyzer`
- Migrations: `alembic upgrade head`
- Install: `pip install -r requirements.txt`
- Run API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Run Celery: `celery -A app.celery_app worker --loglevel=info`
- Run beat (cleanup): `celery -A app.celery_app beat --loglevel=info`

## Tests

```bash
pytest tests/ -v
```

## Project structure

See [docs/development_plan.md](docs/development_plan.md) for the full roadmap and phase status.

## Tech stack

FastAPI · OpenAI GPT-4o · PyPDF2 / pdfplumber · python-docx · SQLAlchemy · Alembic · PostgreSQL · Redis · Celery · Flower · Docker · SlowAPI
