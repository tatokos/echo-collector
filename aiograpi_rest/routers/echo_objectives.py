from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from aiograpi_rest.routers.echo import _require_admin, _supabase_request

router = APIRouter(prefix="/echo", tags=["Echo"])


class ObjectiveInput(BaseModel):
    objective: str = Field(min_length=3, max_length=500)
    priority: int = Field(default=50, ge=0, le=100)


@router.get("/objectives")
async def echo_objectives() -> dict[str, Any]:
    rows = _supabase_request(
        "GET",
        "objectives",
        params={
            "select": "id,objective,priority,enabled,created_at,updated_at",
            "order": "priority.desc,created_at.desc",
        },
    ) or []
    return {"count": len(rows), "items": rows}


@router.post("/objectives")
async def echo_add_objective(
    item: ObjectiveInput,
    x_echo_admin_key: str | None = Header(None, alias="X-Echo-Admin-Key"),
) -> dict[str, Any]:
    _require_admin(x_echo_admin_key)
    objective = item.objective.strip()
    if not objective:
        raise HTTPException(status_code=422, detail="Objective is required")

    existing = _supabase_request(
        "GET",
        "objectives",
        params={
            "select": "id,objective,priority,enabled,created_at,updated_at",
            "objective": f"eq.{objective}",
            "limit": "1",
        },
    ) or []

    if existing:
        rows = _supabase_request(
            "PATCH",
            "objectives",
            params={"id": f"eq.{existing[0]['id']}"},
            payload={"priority": item.priority, "enabled": True},
            prefer="return=representation",
        ) or []
        return rows[0] if rows else existing[0]

    rows = _supabase_request(
        "POST",
        "objectives",
        payload={"objective": objective, "priority": item.priority, "enabled": True},
        prefer="return=representation",
    ) or []
    if not rows:
        raise HTTPException(status_code=502, detail="Could not save objective")
    return rows[0]


@router.delete("/objectives/{objective_id}")
async def echo_delete_objective(
    objective_id: str,
    x_echo_admin_key: str | None = Header(None, alias="X-Echo-Admin-Key"),
) -> dict[str, str]:
    _require_admin(x_echo_admin_key)
    _supabase_request(
        "DELETE",
        "objectives",
        params={"id": f"eq.{objective_id}"},
        prefer="return=minimal",
    )
    return {"status": "deleted"}
