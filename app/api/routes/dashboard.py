"""
Dashboard stats and improvement trend (Phase 6).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import Analysis
from app.models.job_match import JobMatch
from app.models.resume import Resume

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    summary="Dashboard stats",
    description="Total resumes, average/best score, total job matches.",
)
def dashboard_stats(db: Session = Depends(get_db)):
    total_resumes = db.query(Resume).count()
    total_job_matches = db.query(JobMatch).count()
    done = db.query(Analysis).filter(Analysis.status == "done").all()
    scores = [a.overall_score for a in done if a.overall_score is not None]
    average_score = round(sum(scores) / len(scores), 0) if scores else 0
    best_score = max(scores) if scores else 0
    return {
        "total_resumes": total_resumes,
        "average_score": int(average_score),
        "best_score": int(best_score),
        "total_job_matches": total_job_matches,
    }


@router.get(
    "/improvement-trend",
    summary="Improvement trend",
    description="Score over time (list of overall_score by creation order).",
)
def improvement_trend(db: Session = Depends(get_db), limit: int = 20):
    rows = (
        db.query(Analysis.overall_score)
        .filter(Analysis.status == "done", Analysis.overall_score.isnot(None))
        .order_by(Analysis.created_at.asc())
        .limit(limit)
        .all()
    )
    improvement_over_time = [r[0] for r in rows]
    return {"improvement_over_time": improvement_over_time}
