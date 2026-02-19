"""
Celery tasks: async resume analysis, PDF report generation, cleanup.
"""
from pathlib import Path
from uuid import UUID

from app.celery_app import celery_app
from app.config import get_settings
from app.database import SessionLocal
from app.models.analysis import Analysis
from app.models.resume import Resume
from app.services.ai_analyzer import analyze_resume_with_openai


@celery_app.task(bind=True, name="app.tasks.celery_tasks.analyze_resume_async")
def analyze_resume_async(self, resume_id: str, analysis_id: str):
    """
    Run AI analysis in background. Updates Analysis record when done.
    """
    db = SessionLocal()
    try:
        analysis_obj = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis_obj:
            return {"status": "error", "message": "Analysis not found"}
        resume = db.query(Resume).filter(Resume.id == UUID(resume_id)).first()
        if not resume:
            analysis_obj.status = "failed"
            db.commit()
            return {"status": "error", "message": "Resume not found"}
        text = (resume.parsed_text or "").strip()
        if not text:
            analysis_obj.status = "failed"
            db.commit()
            return {"status": "error", "message": "No text to analyze"}
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
        else:
            analysis_obj.status = "failed"
        db.commit()
        return {"status": analysis_obj.status, "analysis_id": analysis_id}
    finally:
        db.close()


@celery_app.task(name="app.tasks.celery_tasks.generate_pdf_report")
def generate_pdf_report(analysis_id: str):
    """
    Generate a simple text report for an analysis (PDF can be added later with reportlab/weasyprint).
    """
    db = SessionLocal()
    try:
        analysis_obj = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis_obj:
            return {"status": "error", "message": "Analysis not found"}
        out_dir = Path(get_settings().upload_dir) / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"report_{analysis_id}.txt"
        lines = [
            f"Resume Analysis Report — {analysis_id}",
            f"Overall Score: {analysis_obj.overall_score or 'N/A'}",
            f"Experience Level: {analysis_obj.experience_level or 'N/A'}",
            "Strengths: " + ", ".join(analysis_obj.strengths or []),
            "Weaknesses: " + ", ".join(analysis_obj.weaknesses or []),
            "Suggestions: " + "; ".join(analysis_obj.suggestions or []),
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        return {"status": "ok", "path": str(path)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.celery_tasks.cleanup_old_files")
def cleanup_old_files():
    """
    Delete local files for resumes older than 30 days; keep DB records for history.
    """
    from datetime import datetime, timedelta
    from app.models.resume import Resume
    upload_dir = Path(get_settings().upload_dir)
    if not upload_dir.exists():
        return {"deleted": 0}
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        old = db.query(Resume).filter(Resume.uploaded_at < cutoff).all()
        deleted = 0
        for r in old:
            if r.local_path:
                p = Path(r.local_path)
                if p.exists():
                    p.unlink(missing_ok=True)
                    deleted += 1
        db.commit()
        reports_dir = upload_dir / "reports"
        if reports_dir.exists():
            cutoff_ts = (cutoff - timedelta(days=30)).timestamp()
            for f in reports_dir.iterdir():
                if f.is_file() and f.stat().st_mtime < cutoff_ts:
                    f.unlink(missing_ok=True)
                    deleted += 1
        return {"deleted": deleted}
    finally:
        db.close()
