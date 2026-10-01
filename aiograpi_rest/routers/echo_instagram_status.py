import os

from fastapi import APIRouter

router = APIRouter(prefix="/echo/instagram", tags=["Echo"])


@router.get("/status")
async def instagram_status() -> dict[str, object]:
    configured = bool(os.getenv("INSTAGRAM_SESSION_ID", "").strip())
    return {
        "configured": configured,
        "status": "connected" if configured else "disconnected",
    }
