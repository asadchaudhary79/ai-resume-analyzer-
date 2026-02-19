"""
Scoring logic — can normalize or compute scores from AI output.
AI returns 0–100; we persist as-is. This module is for any server-side scoring rules.
"""
from typing import Any, Dict


def clamp_score(score: int) -> int:
    """Clamp score to 0–100."""
    return max(0, min(100, score))


def normalize_section_scores(section_scores: Dict[str, Any]) -> Dict[str, int]:
    """Ensure section_scores has int values 0–100."""
    result = {}
    for k, v in (section_scores or {}).items():
        try:
            result[k] = clamp_score(int(v))
        except (TypeError, ValueError):
            result[k] = 50
    for key in ("experience", "skills", "education", "formatting"):
        if key not in result:
            result[key] = 50
    return result
