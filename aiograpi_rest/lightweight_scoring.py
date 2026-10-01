from datetime import datetime, timezone
from typing import Any

from aiograpi_rest.objective_matcher import classify, combine_scores, score_objectives
from aiograpi_rest.routers.echo import _score_post, _supabase_request


def load_objectives() -> list[dict[str, Any]]:
    return _supabase_request(
        "GET",
        "objectives",
        params={
            "select": "id,objective,priority,enabled",
            "enabled": "eq.true",
            "order": "priority.desc",
        },
    ) or []


def score_text(text: str, username: str, keywords: list[dict[str, Any]], objectives: list[dict[str, Any]]) -> dict[str, Any]:
    keyword_score, _, keyword_reason = _score_post({"username": username, "caption": text}, keywords)
    objective = score_objectives(text, objectives)
    objective_score = int(objective.get("score", 0))
    final_score = combine_scores(keyword_score, objective_score)

    reasons: list[str] = []
    if keyword_score:
        reasons.append(keyword_reason)
    if objective_score:
        reasons.append(str(objective.get("reason") or "Objective match"))

    return {
        "keyword_score": keyword_score,
        "objective_score": objective_score,
        "final_score": final_score,
        "relevance": classify(final_score),
        "reason": " · ".join(reasons) if reasons else "No configured signal matched",
        "matched_objective": objective.get("matched_objective"),
        "matched_objective_id": objective.get("matched_objective_id"),
        "engine": "echo-lightweight-v1",
    }


def _existing_instagram_ids(posts: list[dict[str, Any]]) -> set[str]:
    ids = sorted({str(post.get("instagram_id", "")).strip() for post in posts if post.get("instagram_id")})
    if not ids:
        return set()
    rows = _supabase_request(
        "GET",
        "posts",
        params={
            "select": "instagram_id",
            "instagram_id": f"in.({','.join(ids)})",
        },
    ) or []
    return {str(row.get("instagram_id")) for row in rows if row.get("instagram_id")}


def upsert_posts_lightweight(
    source_id: str,
    posts: list[dict[str, Any]],
    keywords: list[dict[str, Any]],
) -> int:
    if not posts:
        return 0

    existing_ids = _existing_instagram_ids(posts)
    incoming_ids = {str(post.get("instagram_id")) for post in posts if post.get("instagram_id")}
    genuinely_new = len(incoming_ids - existing_ids)

    objectives = load_objectives()
    rows: list[dict[str, Any]] = []
    for post in posts:
        result = score_text(post.get("caption", ""), post.get("username", ""), keywords, objectives)
        rows.append(
            {
                **post,
                "source_id": source_id,
                "relevance_score": result["final_score"],
                "relevance": result["relevance"],
                "reason": result["reason"],
                "status": "new",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    _supabase_request(
        "POST",
        "posts",
        params={"on_conflict": "instagram_id"},
        payload=rows,
        prefer="resolution=merge-duplicates,return=minimal",
    )
    return genuinely_new
