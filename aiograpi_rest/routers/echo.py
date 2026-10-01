import os
import secrets
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from aiograpi_rest.dependencies import ClientStorage, get_clients, get_sessionid

router = APIRouter(prefix="/echo", tags=["Echo"])


class SourceInput(BaseModel):
    username: str = Field(min_length=1, max_length=100)


class KeywordInput(BaseModel):
    keyword: str = Field(min_length=1, max_length=120)
    weight: int = Field(default=25, ge=-100, le=100)


class PostStatusInput(BaseModel):
    status: str


def _as_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _normalize_media(media: Any, fallback_username: str) -> dict[str, Any]:
    code = _as_string(getattr(media, "code", None))
    taken_at = getattr(media, "taken_at", None)
    author = getattr(media, "user", None)
    username = getattr(author, "username", None) or fallback_username
    product_type = _as_string(getattr(media, "product_type", None))
    permalink_type = "reel" if (product_type or "").lower() in {"clips", "reels", "reel"} else "p"

    return {
        "instagram_id": _as_string(getattr(media, "pk", None)),
        "code": code,
        "permalink": f"https://www.instagram.com/{permalink_type}/{code}/" if code else None,
        "username": username,
        "caption": getattr(media, "caption_text", "") or "",
        "published_at": taken_at.isoformat() if hasattr(taken_at, "isoformat") else _as_string(taken_at),
        "media_type": getattr(media, "media_type", None),
        "product_type": product_type,
        "thumbnail_url": _as_string(getattr(media, "thumbnail_url", None)),
        "video_url": _as_string(getattr(media, "video_url", None)),
        "like_count": getattr(media, "like_count", None),
        "comment_count": getattr(media, "comment_count", None),
    }


def _require_admin(admin_key: str | None) -> None:
    expected = os.getenv("ECHO_ADMIN_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Echo configuration access is not enabled")
    if not admin_key or not secrets.compare_digest(admin_key, expected):
        raise HTTPException(status_code=401, detail="Invalid Echo admin key")


def _supabase_headers() -> dict[str, str]:
    publishable_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    ingest_key = os.getenv("ECHO_INGEST_KEY", "")
    if not publishable_key or not ingest_key:
        raise HTTPException(status_code=503, detail="Echo database integration is not configured")
    return {
        "apikey": publishable_key,
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
        raise HTTPException(status_code=502, detail=f"Supabase request failed ({response.status_code})")
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
            score += int(item.get("weight", 0))
            matches.append(keyword)
    score = max(0, min(score, 100))
    relevance = "ALTA" if score >= 80 else "MEDIA" if score >= 50 else "BASSA" if score >= 25 else "SCARTATA"
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


@router.get("/health")
async def echo_health() -> dict[str, str]:
    return {"service": "echo-collector", "status": "ok"}


@router.get("/feed")
async def echo_feed(
    limit: int = Query(40, ge=1, le=100),
    relevance: str | None = Query(None),
    status: str | None = Query(None),
) -> dict[str, Any]:
    params = {
        "select": "id,instagram_id,code,permalink,username,caption,thumbnail_url,video_url,published_at,media_type,product_type,like_count,comment_count,relevance_score,relevance,reason,status,created_at",
        "order": "published_at.desc.nullslast,created_at.desc",
        "limit": str(limit),
    }
    if relevance and relevance.upper() in {"ALTA", "MEDIA", "BASSA", "SCARTATA"}:
        params["relevance"] = f"eq.{relevance.upper()}"
    if status and status.lower() in {"new", "reviewed", "ignored"}:
        params["status"] = f"eq.{status.lower()}"
    rows = _supabase_request("GET", "posts", params=params) or []
    return {"count": len(rows), "items": rows}


@router.patch("/posts/{post_id}/status")
async def echo_update_post_status(
    post_id: str,
    item: PostStatusInput,
    x_echo_admin_key: str | None = Header(None, alias="X-Echo-Admin-Key"),
) -> dict[str, str]:
    _require_admin(x_echo_admin_key)
    status = item.status.strip().lower()
    if status not in {"new", "reviewed", "ignored"}:
        raise HTTPException(status_code=422, detail="Invalid post status")
    _supabase_request(
        "PATCH",
        "posts",
        params={"id": f"eq.{post_id}"},
        payload={"status": status, "updated_at": datetime.now(timezone.utc).isoformat()},
        prefer="return=minimal",
    )
    return {"status": status}


@router.get("/sources")
async def echo_sources() -> dict[str, Any]:
    rows = _supabase_request(
        "GET",
        "sources",
        params={"select": "id,platform,username,enabled,last_scanned_at,created_at", "order": "username.asc"},
    ) or []
    return {"count": len(rows), "items": rows}


@router.post("/sources")
async def echo_add_source(source: SourceInput, x_echo_admin_key: str | None = Header(None, alias="X-Echo-Admin-Key")) -> dict[str, Any]:
    _require_admin(x_echo_admin_key)
    username = source.username.strip().lstrip("@").lower()
    if not username:
        raise HTTPException(status_code=422, detail="Instagram username is required")
    return _upsert_source(username)


@router.delete("/sources/{source_id}")
async def echo_delete_source(source_id: str, x_echo_admin_key: str | None = Header(None, alias="X-Echo-Admin-Key")) -> dict[str, str]:
    _require_admin(x_echo_admin_key)
    _supabase_request("DELETE", "sources", params={"id": f"eq.{source_id}"}, prefer="return=minimal")
    return {"status": "deleted"}


@router.get("/keywords")
async def echo_keywords() -> dict[str, Any]:
    rows = _supabase_request("GET", "keywords", params={"select": "id,keyword,weight,enabled,created_at", "order": "keyword.asc"}) or []
    return {"count": len(rows), "items": rows}


@router.post("/keywords")
async def echo_add_keyword(item: KeywordInput, x_echo_admin_key: str | None = Header(None, alias="X-Echo-Admin-Key")) -> dict[str, Any]:
    _require_admin(x_echo_admin_key)
    keyword = item.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=422, detail="Keyword is required")
    existing = _supabase_request("GET", "keywords", params={"select": "id,keyword,weight,enabled,created_at", "keyword": f"ilike.{keyword}", "limit": "1"}) or []
    if existing:
        rows = _supabase_request("PATCH", "keywords", params={"id": f"eq.{existing[0]['id']}"}, payload={"weight": item.weight, "enabled": True}, prefer="return=representation") or []
        return rows[0] if rows else existing[0]
    rows = _supabase_request("POST", "keywords", payload={"keyword": keyword, "weight": item.weight, "enabled": True}, prefer="return=representation") or []
    if not rows:
        raise HTTPException(status_code=502, detail="Could not save keyword")
    return rows[0]


@router.delete("/keywords/{keyword_id}")
async def echo_delete_keyword(keyword_id: str, x_echo_admin_key: str | None = Header(None, alias="X-Echo-Admin-Key")) -> dict[str, str]:
    _require_admin(x_echo_admin_key)
    _supabase_request("DELETE", "keywords", params={"id": f"eq.{keyword_id}"}, prefer="return=minimal")
    return {"status": "deleted"}


@router.get("/preview")
async def echo_preview(
    username: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, Any]:
    clean_username = username.strip().lstrip("@")
    cl = await clients.get(sessionid)
    user = await cl.user_info_by_username_v1(clean_username)
    items, next_cursor = await cl.user_medias_paginated_v1(str(user.pk), limit, "")
    posts = [_normalize_media(media, clean_username) for media in items]
    return {"source": "instagram", "username": clean_username, "count": len(posts), "posts": posts, "next_cursor": next_cursor or ""}


@router.post("/scan")
async def echo_scan(
    username: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20),
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, Any]:
    """Manual scan using the same lightweight Objective + keyword engine as automation."""
    from aiograpi_rest.lightweight_scoring import upsert_posts_lightweight

    clean_username = username.strip().lstrip("@")
    source = _upsert_source(clean_username)
    scan_rows = _supabase_request("POST", "scan_runs", payload={"source_id": source["id"], "status": "running"}, prefer="return=representation")
    scan_id = scan_rows[0]["id"]
    try:
        cl = await clients.get(sessionid)
        user = await cl.user_info_by_username_v1(clean_username)
        items, _ = await cl.user_medias_paginated_v1(str(user.pk), limit, "")
        posts = [_normalize_media(media, clean_username) for media in items]
        stored_count = upsert_posts_lightweight(source["id"], posts, _load_keywords())
        finished_at = datetime.now(timezone.utc).isoformat()
        _supabase_request("PATCH", "scan_runs", params={"id": f"eq.{scan_id}"}, payload={"status": "success", "finished_at": finished_at, "posts_found": len(posts), "posts_new": stored_count}, prefer="return=minimal")
        _supabase_request("PATCH", "sources", params={"id": f"eq.{source['id']}"}, payload={"last_scanned_at": finished_at}, prefer="return=minimal")
        return {"status": "success", "username": clean_username, "posts_found": len(posts), "posts_stored": stored_count, "scan_id": scan_id, "engine": "echo-lightweight-v1"}
    except Exception as exc:
        _supabase_request("PATCH", "scan_runs", params={"id": f"eq.{scan_id}"}, payload={"status": "error", "finished_at": datetime.now(timezone.utc).isoformat(), "error_message": str(exc)[:500]}, prefer="return=minimal")
        raise
