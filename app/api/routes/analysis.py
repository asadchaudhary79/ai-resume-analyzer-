"""
Analysis and job-matching routes.
"""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import Analysis
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.schemas.analysis import (
    AnalysisResponse,
    AnalyzeResponse,
    MatchJobRequest,
    MatchJobResponse,
)
from app.services.ai_analyzer import analyze_resume_with_openai
from app.services.job_matcher import match_resume_to_job

router = APIRouter(prefix="/analysis", tags=["Analysis"])

# Optional Redis cache for analysis (avoid duplicate OpenAI calls)
def _get_cached_analysis(resume_id: UUID) -> dict | None:
    try:
        from app.config import get_settings
        import redis
        r = redis.from_url(get_settings().redis_url)
        key = f"analysis:resume:{resume_id}"
        raw = r.get(key)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


def _set_cached_analysis(resume_id: UUID, data: dict, ttl: int = 3600) -> None:
    try:
        from app.config import get_settings
        import redis
        r = redis.from_url(get_settings().redis_url)
        r.setex(f"analysis:resume:{resume_id}", ttl, json.dumps(data))
    except Exception:
        pass


@router.post(
    "/analyze/{resume_id}",
    response_model=AnalyzeResponse,
    status_code=200,
    summary="Analyze resume",
    description="Run AI analysis (sync or background). Use ?background=true for 202 + Celery; poll GET /analysis/{analysis_id} for result.",
    responses={202: {"description": "Analysis started in background; poll GET /analysis/{analysis_id}"}},
)
def analyze_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    background: bool = False,
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    text = (resume.parsed_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Resume has no extractable text to analyze")

    # Optional: return cached analysis if exists (sync only)
    if not background:
        cached = _get_cached_analysis(resume_id)
        if cached:
            existing = db.query(Analysis).filter(
                Analysis.resume_id == resume_id,
                Analysis.status == "done",
            ).order_by(Analysis.created_at.desc()).first()
            if existing:
                return AnalyzeResponse(analysis_id=existing.id, status="done", message="From cache")

    # Create pending analysis
    analysis_obj = Analysis(resume_id=resume_id, status="pending")
    db.add(analysis_obj)
    db.commit()
    db.refresh(analysis_obj)

    if background:
        from app.tasks.celery_tasks import analyze_resume_async
        task = analyze_resume_async.delay(str(resume_id), str(analysis_obj.id))
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=202,
            content={
                "analysis_id": str(analysis_obj.id),
                "task_id": task.id,
                "status": "pending",
                "message": "Analysis started. Poll GET /api/v1/analysis/{analysis_id} for result.",
            },
        )

    result = analyze_resume_with_openai(text)
    if result:
        analysis_obj.overall_score = result.get("overall_score")
        analysis_obj.section_scores = result.get("section_scores")
        analysis_obj.strengths = result.get("strengths")
        analysis_obj.weaknesses = result.get("weaknesses")
        analysis_obj.suggestions = result.get("suggestions")
        analysis_obj.ats_keywords_missing = result.get("ats_keywords_missing")
        analysis_obj.experience_level = result.get("experience_level")
        analysis_obj.status = "done"
        _set_cached_analysis(resume_id, result)
    else:
        analysis_obj.status = "failed"
    db.commit()
    db.refresh(analysis_obj)
    return AnalyzeResponse(
        analysis_id=analysis_obj.id,
        status=analysis_obj.status,
        message="Analysis completed" if analysis_obj.status == "done" else "Analysis failed",
    )


@router.get(
    "/history",
    response_model=list[AnalysisResponse],
    summary="Analysis history",
    description="List recent analyses.",
)
def list_analyses(db: Session = Depends(get_db), limit: int = 50):
    items = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(limit).all()
    return items


@router.post(
    "/match-job",
    response_model=MatchJobResponse,
    status_code=200,
    summary="Match resume to job",
)
def match_job(body: MatchJobRequest, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == body.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    text = (resume.parsed_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Resume has no text to match")
    if not (body.job_description or body.job_description.strip()):
        raise HTTPException(status_code=400, detail="job_description is required")

    result = match_resume_to_job(text, body.job_description.strip())
    match_record = JobMatch(
        resume_id=body.resume_id,
        job_description=body.job_description[:10000],
        match_score=result["match_score"],
        matched_keywords=result["matched_keywords"],
        missing_keywords=result["missing_keywords"],
        recommendation=result["recommendation"],
        should_apply=1 if result["should_apply"] else 0,
    )
    db.add(match_record)
    db.commit()
    db.refresh(match_record)
    return MatchJobResponse(
        match_score=result["match_score"],
        matched_keywords=result["matched_keywords"],
        missing_keywords=result["missing_keywords"],
        recommendation=result["recommendation"],
        should_apply=result["should_apply"],
        match_id=match_record.id,
        created_at=match_record.created_at,
    )


@router.get(
    "/match-history",
    response_model=list[MatchJobResponse],
    summary="Match history",
)
def match_history(db: Session = Depends(get_db), limit: int = 50):
    rows = db.query(JobMatch).order_by(JobMatch.created_at.desc()).limit(limit).all()
    return [
        MatchJobResponse(
            match_score=r.match_score,
            matched_keywords=r.matched_keywords or [],
            missing_keywords=r.missing_keywords or [],
            recommendation=r.recommendation or "",
            should_apply=bool(r.should_apply),
            match_id=r.id,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Get analysis by ID",
)
def get_analysis(analysis_id: UUID, db: Session = Depends(get_db)):
    analysis_obj = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis_obj:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_obj
