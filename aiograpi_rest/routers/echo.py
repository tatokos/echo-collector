import os
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Query

from aiograpi_rest.dependencies import ClientStorage, get_clients, get_sessionid

router = APIRouter(prefix="/echo", tags=["Echo"])


def _as_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _normalize_media(media: Any, fallback_username: str) -> dict[str, Any]:
    code = _as_string(getattr(media, "code", None))
    taken_at = getattr(media, "taken_at", None)
    author = getattr(media, "user", None)
    username = getattr(author, "username", None) or fallback_username

    return {
        "instagram_id": _as_string(getattr(media, "pk", None)),
        "code": code,
        "permalink": f"https://www.instagram.com/p/{code}/" if code else None,
        "username": username,
        "caption": getattr(media, "caption_text", "") or "",
        "published_at": taken_at.isoformat() if hasattr(taken_at, "isoformat") else _as_string(taken_at),
        "media_type": getattr(media, "media_type", None),
        "product_type": getattr(media, "product_type", None),
        "thumbnail_url": _as_string(getattr(media, "thumbnail_url", None)),
        "video_url": _as_string(getattr(media, "video_url", None)),
        "like_count": getattr(media, "like_count", None),
        "comment_count": getattr(media, "comment_count", None),
    }


def _supabase_headers() -> dict[str, str]:
    publishable_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    ingest_key = os.getenv("ECHO_INGEST_KEY", "")
    if not publishable_key or not ingest_key:
        raise HTTPException(status_code=503, detail="Echo database integration is not configured")
    return {
        "apikey": publishable_key,
        "Authorization": f"Bearer {publishable_key}",
        "Content-Type": "application/json",
        "x-echo-key": ingest_key,
    }


def _supabase_request(
    method: str,
    path: str,
    *,
    params: dict[str, str] | None = None,
    payload: Any = None,
    prefer: str | None = None,
) -> Any:
    base_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not base_url:
        raise HTTPException(status_code=503, detail="Echo database integration is not configured")

    headers = _supabase_headers()
    if prefer:
        headers["Prefer"] = prefer

    response = requests.request(
        method,
        f"{base_url}/rest/v1/{path}",
        params=params,
        json=payload,
        headers=headers,
        timeout=20,
    )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Supabase request failed ({response.status_code})",
        )
    if not response.content:
        return None
    return response.json()


def _load_keywords() -> list[dict[str, Any]]:
    result = _supabase_request(
        "GET",
        "keywords",
        params={"select": "keyword,weight", "enabled": "eq.true"},
    )
    return result or []


def _score_post(post: dict[str, Any], keywords: list[dict[str, Any]]) -> tuple[int, str, str]:
    haystack = f"{post.get('username', '')} {post.get('caption', '')}".lower()
    matches: list[str] = []
    score = 0

    for item in keywords:
        keyword = str(item.get("keyword", "")).strip()
        if keyword and keyword.lower() in haystack:
            weight = int(item.get("weight", 0))
            score += weight
            matches.append(keyword)

    score = max(0, min(score, 100))
    if score >= 80:
        relevance = "ALTA"
    elif score >= 50:
        relevance = "MEDIA"
    elif score >= 25:
        relevance = "BASSA"
    else:
        relevance = "SCARTATA"

    reason = "Matched: " + ", ".join(matches) if matches else "No configured keyword matched"
    return score, relevance, reason


def _upsert_source(username: str) -> dict[str, Any]:
    rows = _supabase_request(
        "POST",
        "sources",
        params={"on_conflict": "platform,username"},
        payload={"platform": "instagram", "username": username, "enabled": True},
        prefer="resolution=merge-duplicates,return=representation",
    )
    if not rows:
        raise HTTPException(status_code=502, detail="Could not create or load Echo source")
    return rows[0]


def _upsert_posts(source_id: str, posts: list[dict[str, Any]], keywords: list[dict[str, Any]]) -> int:
    if not posts:
        return 0

    rows: list[dict[str, Any]] = []
    for post in posts:
        score, relevance, reason = _score_post(post, keywords)
        rows.append(
            {
                **post,
                "source_id": source_id,
                "relevance_score": score,
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


@router.get("/health")
async def echo_health() -> dict[str, str]:
    return {"service": "echo-collector", "status": "ok"}


@router.get("/preview")
async def echo_preview(
    username: str = Query(..., min_length=1, description="Public Instagram username to inspect."),
    limit: int = Query(5, ge=1, le=20),
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, Any]:
    """Return a normalized preview of a public Instagram profile's latest posts."""
    clean_username = username.strip().lstrip("@")
    cl = await clients.get(sessionid)
    user = await cl.user_info_by_username_v1(clean_username)
    items, next_cursor = await cl.user_medias_paginated_v1(str(user.pk), limit, "")

    posts = [_normalize_media(media, clean_username) for media in items]
    return {
        "source": "instagram",
        "username": clean_username,
        "count": len(posts),
        "posts": posts,
        "next_cursor": next_cursor or "",
    }


@router.post("/scan")
async def echo_scan(
    username: str = Query(..., min_length=1, description="Public Instagram username to scan."),
    limit: int = Query(20, ge=1, le=50),
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, Any]:
    """Scan a public Instagram profile, score its posts, and persist them to Echo."""
    clean_username = username.strip().lstrip("@")
    source = _upsert_source(clean_username)
    scan_rows = _supabase_request(
        "POST",
        "scan_runs",
        payload={"source_id": source["id"], "status": "running"},
        prefer="return=representation",
    )
    scan_id = scan_rows[0]["id"]

    try:
        cl = await clients.get(sessionid)
        user = await cl.user_info_by_username_v1(clean_username)
        items, _ = await cl.user_medias_paginated_v1(str(user.pk), limit, "")
        posts = [_normalize_media(media, clean_username) for media in items]
        keywords = _load_keywords()
        stored_count = _upsert_posts(source["id"], posts, keywords)
        finished_at = datetime.now(timezone.utc).isoformat()

        _supabase_request(
            "PATCH",
            "scan_runs",
            params={"id": f"eq.{scan_id}"},
            payload={
                "status": "success",
                "finished_at": finished_at,
                "posts_found": len(posts),
                "posts_new": stored_count,
            },
            prefer="return=minimal",
        )
        _supabase_request(
            "PATCH",
            "sources",
            params={"id": f"eq.{source['id']}"},
            payload={"last_scanned_at": finished_at},
            prefer="return=minimal",
        )

        return {
            "status": "success",
            "username": clean_username,
            "posts_found": len(posts),
            "posts_stored": stored_count,
            "scan_id": scan_id,
        }
    except Exception as exc:
        _supabase_request(
            "PATCH",
            "scan_runs",
            params={"id": f"eq.{scan_id}"},
            payload={
                "status": "failed",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "error_message": str(exc)[:500],
            },
            prefer="return=minimal",
        )
        raise
