"""
Resume upload and CRUD routes.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeListResponse, ResumeResponse
from app.services.pdf_parser import ALLOWED_EXTENSIONS, parse_resume_file
from app.utils.file_handler import delete_file, get_upload_dir

router = APIRouter(prefix="/resumes", tags=["Resumes"])

MAX_SIZE_BYTES = get_settings().max_upload_size_mb * 1024 * 1024


def validate_upload(file: UploadFile) -> None:
    """Validate file type and size."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    # Size is checked when reading in upload handler


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=201,
    summary="Upload resume",
    description="Upload a PDF or DOCX resume (max 5MB). No auth required.",
)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    validate_upload(file)
    content = file.file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {get_settings().max_upload_size_mb}MB",
        )
    import uuid
    upload_dir = get_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename or 'document.pdf'}"
    file_path = str(upload_dir / filename)
    with open(file_path, "wb") as f:
        f.write(content)
    raw_text, parsed_data = parse_resume_file(file_path)
    resume = Resume(
        filename=file.filename or "document.pdf",
        local_path=file_path,
        parsed_text=raw_text or None,
        parsed_data=parsed_data or None,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get(
    "/",
    response_model=list[ResumeListResponse],
    summary="List resumes",
)
def list_resumes(db: Session = Depends(get_db)):
    """List all uploaded resumes."""
    resumes = db.query(Resume).order_by(Resume.uploaded_at.desc()).all()
    return resumes


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get resume",
)
def get_resume(resume_id: UUID, db: Session = Depends(get_db)):
    """Get a single resume by ID."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.delete(
    "/{resume_id}",
    status_code=204,
    summary="Delete resume",
)
def delete_resume(resume_id: UUID, db: Session = Depends(get_db)):
    """Delete resume and its local file."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    delete_file(resume.local_path)
    db.delete(resume)
    db.commit()
    return None
