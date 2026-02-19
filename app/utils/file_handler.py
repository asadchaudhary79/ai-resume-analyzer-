"""
Local file save/delete logic for uploaded resumes.
"""
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from app.config import get_settings


def get_upload_dir() -> Path:
    """Return upload directory path (created on app startup)."""
    return Path(get_settings().upload_dir)


def save_file(file: BinaryIO, original_filename: str) -> str:
    """Save uploaded file to uploads/ with UUID prefix. Returns path string for DB."""
    upload_dir = get_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}_{original_filename}"
    file_path = upload_dir / filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file, buffer)
    return str(file_path)


def delete_file(file_path: str) -> None:
    """Delete file at path (e.g. when resume is deleted)."""
    Path(file_path).unlink(missing_ok=True)
