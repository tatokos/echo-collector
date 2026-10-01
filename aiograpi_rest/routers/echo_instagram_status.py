from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from aiograpi_rest.dependencies import ClientStorage, get_clients
from aiograpi_rest.routers.echo import _supabase_request

router = APIRouter(prefix="/echo/instagram", tags=["Echo"])


def _health() -> dict[str, Any]:
    rows = _supabase_request(
        "GET",
        "instagram_health",
        params={"select": "*", "id": "eq.primary", "limit": "1"},
    ) or []
    return rows[0] if rows else {"state": "healthy", "safe_mode": True}


@router.get("/status")
async def instagram_status(
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, object]:
    configured = clients.has_login()
    health = _health()
    return {
        "configured": configured,
        "status": "connected" if configured else "disconnected",
        "health": health.get("state", "healthy"),
        "safe_mode": bool(health.get("safe_mode", True)),
        "requires_reconnect": bool(health.get("requires_reconnect", False)),
        "paused_until": health.get("paused_until"),
        "last_error_type": health.get("last_error_type"),
        "last_success_at": health.get("last_success_at"),
        "requests_last_run": int(health.get("requests_last_run") or 0),
    }


@router.post("/resume")
async def instagram_resume(
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, object]:
    if not clients.has_login():
        raise HTTPException(status_code=409, detail="Instagram is not connected")
    _supabase_request(
        "PATCH",
        "instagram_health",
        params={"id": "eq.primary"},
        payload={
            "state": "healthy",
            "requires_reconnect": False,
            "paused_until": None,
            "last_error_type": None,
            "last_error": None,
            "consecutive_errors": 0,
        },
        prefer="return=minimal",
    )
    return {"status": "resumed", "health": "healthy"}
