from datetime import datetime, timezone
from typing import Any

from aiograpi_rest.routers.echo import _score_post, _supabase_request
from aiograpi_rest.semantic import analyze_semantics


def _classification(score: int) -> str:
    if score >= 80:
        return "ALTA"
    if score >= 50:
        return "MEDIA"
    if score >= 25:
        return "BASSA"
    return "SCARTATA"


def _load_objectives() -> list[dict[str, Any]]:
    return _supabase_request(
        "GET",
        "objectives",
        params={
            "select": "id,objective,priority,enabled",
            "enabled": "eq.true",
            "order": "priority.desc",
        },
    ) or []


def upsert_posts_hybrid(
    source_id: str,
    posts: list[dict[str, Any]],
    keywords: list[dict[str, Any]],
) -> int:
    if not posts:
        return 0

    objectives = _load_objectives()
    rows: list[dict[str, Any]] = []

    for post in posts:
        keyword_score, _, keyword_reason = _score_post(post, keywords)
        try:
            semantic = analyze_semantics(post.get("caption", ""), objectives)
            semantic_score = int(semantic.get("semantic_score", 0))
            matched_objective = semantic.get("matched_objective")
        except Exception:
            semantic_score = 0
            matched_objective = None

        stronger = max(keyword_score, semantic_score)
        weaker = min(keyword_score, semantic_score)
        final_score = max(0, min(100, round(stronger * 0.85 + weaker * 0.15)))
        relevance = _classification(final_score)

        reasons: list[str] = []
        if keyword_score:
            reasons.append(keyword_reason)
        if matched_objective:
            reasons.append(f"Objective: {matched_objective}")
        reason = " · ".join(reasons) if reasons else "No strong keyword or objective match"

        rows.append(
            {
                **post,
                "source_id": source_id,
                "relevance_score": final_score,
                "relevance": relevance,
                "reason": reason,
                "status": "new",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    stored = _supabase_request(
        "POST",
        "posts",
        params={"on_conflict": "instagram_id"},
        payload=rows,
        prefer="resolution=merge-duplicates,return=representation",
    )
    return len(stored or [])
