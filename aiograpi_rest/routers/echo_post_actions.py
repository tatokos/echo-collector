import os
import secrets

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from aiograpi_rest.routers.echo import _supabase_request

router = APIRouter(prefix="/echo/posts", tags=["Echo"])


class PostStatusInput(BaseModel):
    status: str


def _require_admin(admin_key: str | None) -> None:
    expected = os.getenv("ECHO_ADMIN_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Echo configuration access is not enabled")
    if not admin_key or not secrets.compare_digest(admin_key, expected):
        raise HTTPException(status_code=401, detail="Invalid Echo admin key")


@router.patch("/{post_id}/status")
async def set_post_status(
    post_id: str,
    item: PostStatusInput,
    x_echo_admin_key: str | None = Header(None, alias="X-Echo-Admin-Key"),
) -> dict[str, str]:
    _require_admin(x_echo_admin_key)
    status = item.status.strip().lower()
    if status not in {"new", "reviewed", "ignored"}:
        raise HTTPException(status_code=422, detail="Invalid post status")

    rows = _supabase_request(
        "PATCH",
        "posts",
        params={"id": f"eq.{post_id}"},
        payload={"status": status},
        prefer="return=representation",
    ) or []
    if not rows:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"status": status}
