"""
OpenAI GPT-4o resume analysis — returns structured JSON (scores, strengths, suggestions, etc.).
"""
import json
import re
from typing import Any, Dict, Optional

from app.config import get_settings


SYSTEM_PROMPT = """You are an expert HR consultant and ATS system.
Analyze the resume text provided and return a strict JSON object only (no markdown, no code block).
Use this exact structure:
{
  "overall_score": <0-100 integer>,
  "section_scores": {
    "experience": <0-100>,
    "skills": <0-100>,
    "education": <0-100>,
    "formatting": <0-100>
  },
  "strengths": ["string", ...],
  "weaknesses": ["string", ...],
  "suggestions": ["actionable string", ...],
  "ats_keywords_missing": ["keyword", ...],
  "experience_level": "junior" | "mid" | "senior"
}
Be concise. Return only valid JSON."""


def analyze_resume_with_openai(resume_text: str) -> Optional[Dict[str, Any]]:
    """
    Call OpenAI GPT-4o to analyze resume text. Returns parsed dict or None on failure.
    """
    api_key = get_settings().openai_api_key
    if not api_key:
        return _mock_analysis(resume_text)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this resume:\n\n{resume_text[:12000]}"},
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content
        if not content:
            return _mock_analysis(resume_text)
        # Strip markdown code block if present
        content = re.sub(r"^```(?:json)?\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content)
        data = json.loads(content)
        return _normalize_analysis(data)
    except Exception:
        return _mock_analysis(resume_text)


def _normalize_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all expected keys exist and types are correct."""
    section_scores = data.get("section_scores") or {}
    for key in ("experience", "skills", "education", "formatting"):
        if key not in section_scores:
            section_scores[key] = data.get("overall_score", 50)
    return {
        "overall_score": min(100, max(0, int(data.get("overall_score", 50)))),
        "section_scores": section_scores,
        "strengths": list(data.get("strengths") or [])[:15],
        "weaknesses": list(data.get("weaknesses") or [])[:15],
        "suggestions": list(data.get("suggestions") or [])[:15],
        "ats_keywords_missing": list(data.get("ats_keywords_missing") or [])[:20],
        "experience_level": (
            data.get("experience_level") or "mid"
        ).lower() if isinstance(data.get("experience_level"), str) else "mid",
    }


def _mock_analysis(resume_text: str) -> Dict[str, Any]:
    """Return a placeholder when OpenAI is not configured or fails."""
    return {
        "overall_score": 65,
        "section_scores": {"experience": 60, "skills": 70, "education": 65, "formatting": 65},
        "strengths": ["Resume provided for analysis", "Use OPENAI_API_KEY for full AI analysis"],
        "weaknesses": ["AI analysis not run (no API key or error)"],
        "suggestions": ["Set OPENAI_API_KEY in .env and re-run analysis"],
        "ats_keywords_missing": [],
        "experience_level": "mid",
    }
