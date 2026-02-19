"""
Analysis model — stores AI analysis results per resume.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    overall_score = Column(Integer, nullable=True)  # 0–100
    section_scores = Column(JSONB, nullable=True)
    strengths = Column(JSONB, nullable=True)
    weaknesses = Column(JSONB, nullable=True)
    suggestions = Column(JSONB, nullable=True)
    ats_keywords_missing = Column(JSONB, nullable=True)
    experience_level = Column(String(32), nullable=True)  # junior | mid | senior
    status = Column(String(32), default="pending")  # pending | done | failed
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # resume = relationship("Resume", back_populates="analyses")
