"""
Resume model — stores uploaded file metadata and parsed data.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    local_path = Column(String(512), nullable=False)  # e.g. uploads/uuid_filename.pdf
    parsed_text = Column(Text, nullable=True)
    parsed_data = Column(JSONB, nullable=True)  # structured fields as JSON
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # analyses = relationship("Analysis", back_populates="resume")
