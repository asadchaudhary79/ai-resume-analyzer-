"""
JobMatch model — stores job description matching results.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_description = Column(Text, nullable=False)
    match_score = Column(Integer, nullable=False)  # 0-100
    matched_keywords = Column(JSONB, nullable=True)
    missing_keywords = Column(JSONB, nullable=True)
    recommendation = Column(Text, nullable=True)
    should_apply = Column(Integer, nullable=True)  # 1=True, 0=False
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
