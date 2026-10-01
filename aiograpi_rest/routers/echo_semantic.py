from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from aiograpi_rest.routers.echo import _score_post, _supabase_request
from aiograpi_rest.semantic import analyze_semantics

router = APIRouter(prefix="/echo", tags=["Echo"])


class AnalyzeInput(BaseModel):
    text: str = Field(min_length=3, max_length=3000)
    username: str = Field(default="test", max_length=100)


def _classification(score: int) -> str:
    if score >= 80:
        return "ALTA"
    if score >= 50:
        return "MEDIA"
    if score >= 25:
        return "BASSA"
    return "SCARTATA"


@router.post("/analyze")
async def echo_analyze(item: AnalyzeInput) -> dict[str, Any]:
    keywords = _supabase_request(
        "GET",
        "keywords",
        params={"select": "keyword,weight", "enabled": "eq.true"},
    ) or []
    objectives = _supabase_request(
        "GET",
        "objectives",
        params={
            "select": "id,objective,priority,enabled",
            "enabled": "eq.true",
            "order": "priority.desc",
        },
    ) or []

    keyword_score, _, keyword_reason = _score_post(
        {"username": item.username, "caption": item.text}, keywords
    )

    try:
        semantic = analyze_semantics(item.text, objectives)
        semantic_available = True
        semantic_error = None
    except Exception as exc:
        semantic = {
            "semantic_score": 0,
            "similarity": 0.0,
            "matched_objective_id": None,
            "matched_objective": None,
            "model": None,
        }
        semantic_available = False
        semantic_error = str(exc)[:200]

    semantic_score = int(semantic["semantic_score"])
    # Keyword matches are strong explicit evidence. Semantic similarity catches implicit meaning.
    # Taking the stronger signal and a small contribution from the weaker one avoids penalizing
    # posts that are highly relevant by only one route.
    stronger = max(keyword_score, semantic_score)
    weaker = min(keyword_score, semantic_score)
    final_score = max(0, min(100, round(stronger * 0.85 + weaker * 0.15)))
    relevance = _classification(final_score)

    reasons = []
    if keyword_score:
        reasons.append(keyword_reason)
    if semantic.get("matched_objective"):
        reasons.append(f"Objective: {semantic['matched_objective']}")
    reason = " · ".join(reasons) if reasons else "No strong keyword or objective match"

    return {
        "text": item.text,
        "keyword_score": keyword_score,
        "semantic_score": semantic_score,
        "final_score": final_score,
        "relevance": relevance,
        "reason": reason,
        "matched_objective": semantic.get("matched_objective"),
        "similarity": semantic.get("similarity"),
        "semantic_available": semantic_available,
        "semantic_error": semantic_error,
        "model": semantic.get("model"),
    }
