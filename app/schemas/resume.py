"""
Resume request/response schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ResumeBase(BaseModel):
    filename: str
    local_path: str


class ResumeCreate(ResumeBase):
    parsed_text: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None


class ResumeResponse(BaseModel):
    id: UUID
    filename: str
    local_path: str
    parsed_text: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    id: UUID
    filename: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}
