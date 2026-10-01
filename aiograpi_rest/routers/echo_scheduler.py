import os
import secrets
from datetime import datetime, timedelta, timezone
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _health() -> dict[str, Any]:
    rows = _supabase_request(
        "GET",
        "instagram_health",
        params={"select": "*", "id": "eq.primary", "limit": "1"},
    ) or []
    if rows:
        return rows[0]
    return {
        "state": "healthy",
        "requires_reconnect": False,
        "paused_until": None,
        "consecutive_errors": 0,
        "safe_mode": True,
        "max_sources_per_run": 8,
        "max_posts_per_source": 10,
        "min_minutes_between_runs": 50,
    }


def _update_health(**values: Any) -> None:
    _supabase_request(
        "PATCH",
        "instagram_health",
        params={"id": "eq.primary"},
        payload={**values, "updated_at": _now().isoformat()},
        prefer="return=minimal",
    )


def _classify_error(exc: Exception) -> tuple[str, bool, int]:
    name = exc.__class__.__name__.lower()
    text = f"{name} {exc}".lower()

    reconnect_markers = (
        "challenge",
        "loginrequired",
        "login_required",
        "twofactor",
        "checkpoint",
        "consentrequired",
        "consent_required",
        "sentryblock",
    )
    rate_markers = (
        "feedbackrequired",
        "feedback_required",
        "please wait",
        "ratelimit",
        "rate_limit",
        "too many requests",
        "429",
    )

    if any(marker in text for marker in reconnect_markers):
        return "verification_required", True, 24 * 60
    if any(marker in text for marker in rate_markers):
        return "rate_limited", False, 6 * 60
    return "request_error", False, 2 * 60


def _record_failure(exc: Exception, previous_errors: int) -> dict[str, Any]:
    error_type, reconnect, cooldown_minutes = _classify_error(exc)
    errors = previous_errors + 1
    if error_type == "request_error" and errors >= 2:
        cooldown_minutes = 6 * 60
    paused_until = _now() + timedelta(minutes=cooldown_minutes)
    state = "paused" if reconnect or errors >= 2 else "caution"
    _update_health(
        state=state,
        requires_reconnect=reconnect,
        paused_until=paused_until.isoformat(),
        last_error_type=error_type,
        last_error=str(exc)[:300],
        consecutive_errors=errors,
    )
    return {
        "state": state,
        "reason": error_type,
        "requires_reconnect": reconnect,
        "paused_until": paused_until.isoformat(),
    }


async def _scan_one(source: dict[str, Any], limit: int, cl: Any) -> dict[str, Any]:
    username = source["username"]
    source_id = source["id"]
    scan_rows = _supabase_request(
        "POST",
        "scan_runs",
        payload={"source_id": source_id, "status": "running"},
        prefer="return=representation",
    )
    scan_id = scan_rows[0]["id"]

    try:
        user_id = str(source.get("instagram_user_id") or "").strip()
        requests_used = 0
        if not user_id:
            user = await cl.user_info_by_username_v1(username)
            user_id = str(user.pk)
            requests_used += 1
            _supabase_request(
                "PATCH",
                "sources",
                params={"id": f"eq.{source_id}"},
                payload={"instagram_user_id": user_id},
                prefer="return=minimal",
            )

        items, _ = await cl.user_medias_paginated_v1(user_id, limit, "")
        requests_used += 1
        posts = [_normalize_media(media, username) for media in items]
        stored_count = upsert_posts_lightweight(source_id, posts, _load_keywords())
        finished_at = _now().isoformat()

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
            "requests_used": requests_used,
        }
    except Exception as exc:
        _supabase_request(
            "PATCH",
            "scan_runs",
            params={"id": f"eq.{scan_id}"},
            payload={
                "status": "error",
                "finished_at": _now().isoformat(),
                "error_message": str(exc)[:500],
            },
            prefer="return=minimal",
        )
        return {
            "username": username,
            "status": "error",
            "error": str(exc)[:160],
            "exception": exc,
            "requests_used": 0,
        }


@router.post("/scan-enabled")
async def echo_scan_enabled(
    limit: int = Query(10, ge=1, le=20),
    x_echo_automation_key: str | None = Header(None, alias="X-Echo-Automation-Key"),
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, Any]:
    """Conservatively scan enabled Instagram sources with an automatic safety circuit breaker."""
    _require_automation(x_echo_automation_key)
    health = _health()
    now = _now()

    paused_until = _parse_time(health.get("paused_until"))
    if health.get("requires_reconnect"):
        return {
            "status": "paused",
            "reason": "instagram_reconnect_required",
            "health": health.get("state", "paused"),
        }
    if paused_until and paused_until > now:
        return {
            "status": "paused",
            "reason": health.get("last_error_type") or "safety_cooldown",
            "paused_until": paused_until.isoformat(),
            "health": health.get("state", "caution"),
        }

    last_attempt = _parse_time(health.get("last_attempt_at"))
    min_minutes = int(health.get("min_minutes_between_runs") or 50)
    if last_attempt and now - last_attempt < timedelta(minutes=min_minutes):
        return {
            "status": "skipped",
            "reason": "safe_interval_not_elapsed",
            "next_eligible_at": (last_attempt + timedelta(minutes=min_minutes)).isoformat(),
        }

    max_sources = int(health.get("max_sources_per_run") or 8)
    max_posts = int(health.get("max_posts_per_source") or 10)
    safe_limit = min(limit, max_posts)
    _update_health(last_attempt_at=now.isoformat(), requests_last_run=0)

    sources = _supabase_request(
        "GET",
        "sources",
        params={
            "select": "id,username,instagram_user_id,last_scanned_at",
            "platform": "eq.instagram",
            "enabled": "eq.true",
            "order": "last_scanned_at.asc.nullsfirst,username.asc",
            "limit": str(max_sources),
        },
    ) or []

    if not sources:
        _update_health(
            state="healthy",
            requires_reconnect=False,
            consecutive_errors=0,
            last_error_type=None,
            last_error=None,
            paused_until=None,
        )
        return {"status": "success", "enabled_sources": 0, "results": []}

    try:
        cl = await clients.latest()
    except Exception:
        _update_health(state="paused", requires_reconnect=True, last_error_type="login_missing")
        return {
            "status": "paused",
            "reason": "instagram_login_not_configured",
            "enabled_sources": len(sources),
        }

    results = []
    requests_used = 0
    for source in sources:
        result = await _scan_one(source, safe_limit, cl)
        requests_used += int(result.pop("requests_used", 0))
        if result["status"] == "error":
            exc = result.pop("exception")
            safety = _record_failure(exc, int(health.get("consecutive_errors") or 0))
            results.append(result)
            _update_health(requests_last_run=requests_used)
            return {
                "status": "stopped_for_safety",
                "enabled_sources": len(sources),
                "requests_used": requests_used,
                "safety": safety,
                "results": results,
            }
        results.append(result)

    _update_health(
        state="healthy",
        requires_reconnect=False,
        paused_until=None,
        last_error_type=None,
        last_error=None,
        consecutive_errors=0,
        last_success_at=_now().isoformat(),
        requests_last_run=requests_used,
    )
    return {
        "status": "complete",
        "safe_mode": True,
        "enabled_sources": len(sources),
        "successful": len(results),
        "failed": 0,
        "requests_used": requests_used,
        "posts_per_source_limit": safe_limit,
        "results": results,
    }
