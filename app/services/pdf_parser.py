"""
Extract text and structured data from PDF and DOCX resumes.
"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pdfplumber
from docx import Document as DocxDocument

# Fallback if pdfplumber fails (e.g. scanned PDF)
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 5


def extract_text_from_pdf(path: str) -> str:
    """Extract raw text from PDF using pdfplumber, fallback to PyPDF2."""
    path_obj = Path(path)
    if not path_obj.exists():
        return ""

    text_parts: List[str] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
    except Exception:
        if PyPDF2:
            try:
                with open(path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            text_parts.append(t)
            except Exception:
                pass
    return "\n".join(text_parts).strip() if text_parts else ""


def extract_text_from_docx(path: str) -> str:
    """Extract raw text from DOCX."""
    path_obj = Path(path)
    if not path_obj.exists():
        return ""
    try:
        doc = DocxDocument(path)
        return "\n".join(p.text for p in doc.paragraphs).strip()
    except Exception:
        return ""


def extract_text(path: str) -> str:
    """Extract text from PDF or DOCX based on extension."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix == ".docx":
        return extract_text_from_docx(path)
    return ""


# Simple regex-based extraction for name, email, phone
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{8,}")
# Section headers (various forms)
SECTION_HEADERS = re.compile(
    r"^(experience|education|skills|strengths\s*&\s*skills|projects|certificates?|certifications|summary|objective|work\s+history|employment|hobbies|area\s+of\s+strength|languages)\s*[:]?\s*$",
    re.I,
)
# URL pattern
URL_RE = re.compile(r"https?://[^\s]+")


def _name_from_url(url: str) -> str:
    """Derive a short readable name from URL (e.g. https://www.servicebull.com/ -> servicebull.com)."""
    url = url.strip()
    if not url:
        return "Project"
    try:
        # Remove scheme and path, get host (e.g. www.servicebull.com -> servicebull.com)
        after = re.sub(r"^https?://", "", url, flags=re.I)
        host = after.split("/")[0].strip()
        if host.lower().startswith("www."):
            host = host[4:]
        return host if host else "Project"
    except Exception:
        return url[:50] if len(url) > 50 else url


def _section_boundary(line: str) -> bool:
    """True if line looks like a new section header (exact or line starts with header)."""
    if not line or len(line) > 120:
        return False
    lower = line.lower().strip()
    if SECTION_HEADERS.match(line):
        return True
    headers = ("strengths & skills", "area of strength", "certificates", "certifications", "experience", "education", "languages", "skills", "projects", "hobbies")
    for h in headers:
        if lower.startswith(h):
            return True
    return False


def _section_name(line: str) -> str:
    """Get normalized section name from a line that starts with a header."""
    lower = line.lower()
    # "Area of strength" is soft-skills prose; only "Strengths & Skills" (tech list) → skills
    if "area of strength" in lower:
        return "strengths"
    if "strength" in lower and "skill" in lower:
        return "skills"
    if "education" in lower:
        return "education"
    if "experience" in lower:
        return "experience"
    if "project" in lower:
        return "projects"
    if "certificate" in lower or "certification" in lower:
        return "certifications"
    if "language" in lower:
        return "languages"
    if "hobbi" in lower:
        return "hobbies"
    return "other"


def parse_structured_data(raw_text: str) -> Dict[str, Any]:
    """
    Parse structured fields from raw resume text.
    Returns dict with name, email, phone, skills, experience, education, projects, certifications.
    """
    data: Dict[str, Any] = {
        "name": "",
        "email": "",
        "phone": "",
        "skills": [],
        "strengths": [],  # soft-skills prose from "Area of strength", not tokenized
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "languages": [],
    }
    if not raw_text:
        return data

    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    emails = EMAIL_RE.findall(raw_text)
    if emails:
        data["email"] = emails[0]
    phones = PHONE_RE.findall(raw_text)
    if phones:
        data["phone"] = phones[0].strip()

    # Name: first substantial line without @ and not a section header
    for line in lines[:8]:
        if not line or "@" in line or (line[0].isdigit() if line else True):
            continue
        if SECTION_HEADERS.match(line) or line.lower().startswith("http"):
            continue
        if 3 <= len(line) <= 80:
            data["name"] = line
            break

    # Split text into sections by headers (header may have content on same line)
    current_section = None
    section_lines: Dict[str, List[str]] = {}

    for line in lines:
        if _section_boundary(line):
            current_section = _section_name(line)
            # Rest of line after header is first line of content (e.g. "Strengths & Skills HTML/CSS WordPress")
            remainder = line
            headers_order = ("strengths & skills", "area of strength", "certificates", "certifications", "experience", "education", "languages", "skills", "projects", "hobbies")
            for h in headers_order:
                if line.lower().startswith(h):
                    remainder = line[len(h):].strip().lstrip(":").strip()
                    break
            # Merge with existing section instead of overwriting (e.g. "Area of strength" then "Strengths & Skills")
            existing = section_lines.get(current_section, []) if current_section != "other" else []
            section_lines[current_section] = existing
            if remainder:
                section_lines[current_section].append(remainder)
            continue
        if current_section and current_section != "other":
            section_lines.setdefault(current_section, []).append(line)

    # Fallback: if no sections found but text contains header-like words, split by header pattern
    section_headers_pattern = re.compile(
        r"\n\s*(Education|Experience|Strengths?\s*&\s*Skills|Area\s+of\s+Strength|Projects?|Certificates?|Certifications?|Languages?|Hobbies)\s*:?\s*\n",
        re.I,
    )
    has_any_content = any(section_lines.get(s) for s in ("skills", "education", "experience", "projects", "certifications", "languages"))
    if not has_any_content:
        # Try split by newline-based headers first
        if section_headers_pattern.search(raw_text):
            parts = section_headers_pattern.split(raw_text)
            for i in range(1, len(parts) - 1):
                if i % 2 == 0:
                    continue
                header_line = (parts[i] or "").strip()
                block = (parts[i + 1] or "").strip()
                if not header_line:
                    continue
                sec = _section_name(header_line)
                if sec != "other" and block:
                    for ln in (ln.strip() for ln in block.splitlines() if ln.strip()):
                        section_lines.setdefault(sec, []).append(ln)
        else:
            # No newlines before headers (e.g. single-line PDF): split by header words
            single_line_headers = re.compile(
                r"\s+(Education|Experience|Strengths?\s*&\s*Skills|Area\s+of\s+Strength|Projects?|Certificates?|Certifications?|Languages?|Hobbies)\s+(?=[A-Z0-9])",
                re.I,
            )
            parts = single_line_headers.split(raw_text)
            if len(parts) >= 3:
                for i in range(1, len(parts) - 1):
                    if i % 2 == 0:
                        continue
                    header_line = (parts[i] or "").strip()
                    block = (parts[i + 1] or "").strip()
                    if not header_line:
                        continue
                    sec = _section_name(header_line)
                    if sec != "other" and block:
                        for ln in (ln.strip() for ln in re.split(r"\s{2,}|\n", block) if ln.strip() and len(ln) < 500):
                            section_lines.setdefault(sec, []).append(ln)

    # Skills: only from "Strengths & Skills" section (tech list). "Area of strength" → strengths, not tokenized.
    skill_lines = section_lines.get("skills", [])
    seen_skills: set = set()
    for line in skill_lines:
        if _section_boundary(line):
            continue
        # Split by / , \n and collect tokens (e.g. "HTML/CSS/BootStrap", "WordPress" -> HTML, CSS, BootStrap, WordPress)
        parts = re.split(r"[\s/,]+", line)
        for p in parts:
            p = p.strip().strip("-•*").strip()
            if not p or len(p) < 2 or len(p) > 50:
                continue
            if p.isdigit() or p.lower() in ("and", "the", "or", "in", "to", "of", "for"):
                continue
            key = p.lower()
            if key not in seen_skills:
                seen_skills.add(key)
                data["skills"].append(p)
        if len(data["skills"]) >= 150:
            break

    # Strengths: soft-skills prose from "Area of strength" (kept as lines, not tokenized)
    for line in section_lines.get("strengths", []):
        if line and not _section_boundary(line):
            data["strengths"].append(line.strip())

    # Education: all non-empty lines (no skip)
    for line in section_lines.get("education", []):
        if not line or _section_boundary(line):
            continue
        if line.startswith("http") or re.match(r"^[\d\s\-]+$", line):
            continue
        entry = line.strip()
        if entry:
            data["education"].append(entry)

    # Experience: all non-empty lines (company, role, location, etc.)
    for line in section_lines.get("experience", []):
        if not line or _section_boundary(line):
            continue
        if line.startswith("http"):
            continue
        entry = line.strip()
        if entry:
            data["experience"].append(entry)

    # Projects: project names and optional URLs (use domain as name when line is only URL)
    for line in section_lines.get("projects", []):
        if not line or _section_boundary(line):
            continue
        urls = URL_RE.findall(line)
        name = URL_RE.sub("", line).strip().strip("-•*()").strip()
        if name and len(name) > 1:
            data["projects"].append({"name": name, "urls": urls[:3]})
        elif urls:
            data["projects"].append({"name": _name_from_url(urls[0]), "urls": urls[:3]})

    # Certifications: all non-empty lines
    for line in section_lines.get("certifications", []):
        if not line or _section_boundary(line):
            continue
        entry = line.strip()
        if entry:
            data["certifications"].append(entry)

    # Languages: tokens from languages section (e.g. "English Urdu Punjabi")
    for line in section_lines.get("languages", []):
        if not line or _section_boundary(line):
            continue
        for token in re.split(r"[\s,]+", line):
            token = token.strip().strip("-•*").strip()
            if token and len(token) <= 30 and token not in data["languages"]:
                data["languages"].append(token)

    return data


def parse_resume_file(file_path: str) -> tuple[str, Dict[str, Any]]:
    """
    Extract raw text and parsed structured data from a resume file.
    Returns (raw_text, parsed_data).
    """
    raw_text = extract_text(file_path)
    parsed_data = parse_structured_data(raw_text)
    return raw_text, parsed_data
