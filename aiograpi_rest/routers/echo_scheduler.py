import os
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from aiograpi_rest.dependencies import ClientStorage, get_clients
from aiograpi_rest.lightweight_scoring import upsert_posts_lightweight
from aiograpi_rest.routers.echo import (
    _load_keywords,
    _normalize_media,
    _supabase_request,
)

router = APIRouter(prefix="/echo", tags=["Echo"])


def _require_automation(key: str | None) -> None:
    expected = os.getenv("ECHO_AUTOMATION_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Echo automation is not configured")
    if not key or not secrets.compare_digest(key, expected):
        raise HTTPException(status_code=401, detail="Invalid Echo automation key")


async def _scan_one(username: str, source_id: str, limit: int, cl: Any) -> dict[str, Any]:
    scan_rows = _supabase_request(
        "POST",
        "scan_runs",
        payload={"source_id": source_id, "status": "running"},
        prefer="return=representation",
    )
    scan_id = scan_rows[0]["id"]

    try:
        user = await cl.user_info_by_username_v1(username)
        items, _ = await cl.user_medias_paginated_v1(str(user.pk), limit, "")
        posts = [_normalize_media(media, username) for media in items]
        stored_count = upsert_posts_lightweight(source_id, posts, _load_keywords())
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
            params={"id": f"eq.{source_id}"},
            payload={"last_scanned_at": finished_at},
            prefer="return=minimal",
        )
        return {
            "username": username,
            "status": "success",
            "posts_found": len(posts),
            "posts_stored": stored_count,
        }
    except Exception as exc:
        _supabase_request(
            "PATCH",
            "scan_runs",
            params={"id": f"eq.{scan_id}"},
            payload={
                "status": "error",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "error_message": str(exc)[:500],
            },
            prefer="return=minimal",
        )
        return {"username": username, "status": "error", "error": str(exc)[:160]}


@router.post("/scan-enabled")
async def echo_scan_enabled(
    limit: int = Query(20, ge=1, le=50),
    x_echo_automation_key: str | None = Header(None, alias="X-Echo-Automation-Key"),
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, Any]:
    """Automatically scan every enabled Instagram source."""
    _require_automation(x_echo_automation_key)

    sources = _supabase_request(
        "GET",
        "sources",
        params={
            "select": "id,username",
            "platform": "eq.instagram",
            "enabled": "eq.true",
            "order": "username.asc",
        },
    ) or []

    if not sources:
        return {"status": "success", "enabled_sources": 0, "results": []}

    try:
        cl = await clients.latest()
    except Exception:
        return {
            "status": "skipped",
            "reason": "instagram_login_not_configured",
            "enabled_sources": len(sources),
        }

    results = []
    for source in sources:
        results.append(await _scan_one(source["username"], source["id"], limit, cl))

    return {
        "status": "complete",
        "enabled_sources": len(sources),
        "successful": sum(1 for result in results if result["status"] == "success"),
        "failed": sum(1 for result in results if result["status"] == "error"),
        "results": results,
    }
