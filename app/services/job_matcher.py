"""
Job description matching using OpenAI GPT-4o.
Compares resume vs JD and returns match score, keywords, recommendation.
"""
import json
import re
from typing import Any, Dict, List, Optional

from app.config import get_settings


MATCH_SYSTEM_PROMPT = """You are an expert recruiter. Compare the resume with the job description.
Return a strict JSON object only (no markdown):
{
  "match_score": <0-100 integer>,
  "matched_keywords": ["keyword", ...],
  "missing_keywords": ["keyword", ...],
  "recommendation": "One short paragraph",
  "should_apply": true or false
}
Be concise. Return only valid JSON."""


def match_resume_to_job(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Use OpenAI to compare resume vs job description. Returns dict with match_score, lists, recommendation, should_apply.
    """
    api_key = get_settings().openai_api_key
    if not api_key:
        return _mock_match(resume_text, job_description)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": MATCH_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Resume:\n{resume_text[:8000]}\n\nJob description:\n{job_description[:6000]}",
                },
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            return _mock_match(resume_text, job_description)
        content = re.sub(r"^```(?:json)?\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content)
        data = json.loads(content)
        return _normalize_match(data)
    except Exception:
        return _mock_match(resume_text, job_description)


def _normalize_match(data: Dict[str, Any]) -> Dict[str, Any]:
    match_score = min(100, max(0, int(data.get("match_score", 50))))
    return {
        "match_score": match_score,
        "matched_keywords": list(data.get("matched_keywords") or [])[:30],
        "missing_keywords": list(data.get("missing_keywords") or [])[:30],
        "recommendation": str(data.get("recommendation") or "Unable to generate.")[:500],
        "should_apply": bool(data.get("should_apply", match_score >= 50)),
    }


def _mock_match(resume_text: str, job_description: str) -> Dict[str, Any]:
    return {
        "match_score": 50,
        "matched_keywords": [],
        "missing_keywords": [],
        "recommendation": "Set OPENAI_API_KEY for AI-powered job matching.",
        "should_apply": True,
    }
