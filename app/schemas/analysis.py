"""
Analysis and job-match request/response schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class SectionScores(BaseModel):
    experience: int = 0
    skills: int = 0
    education: int = 0
    formatting: int = 0


class AnalysisResponse(BaseModel):
    id: UUID
    resume_id: UUID
    overall_score: Optional[int] = None
    section_scores: Optional[Dict[str, Any]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    ats_keywords_missing: Optional[List[str]] = None
    experience_level: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyzeResponse(BaseModel):
    """Response after triggering analysis (sync or async)."""
    analysis_id: UUID
    status: str  # done | pending
    message: Optional[str] = None


class MatchJobRequest(BaseModel):
    resume_id: UUID
    job_description: str


class MatchJobResponse(BaseModel):
    match_score: int
    matched_keywords: List[str]
    missing_keywords: List[str]
    recommendation: str
    should_apply: bool
    match_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
