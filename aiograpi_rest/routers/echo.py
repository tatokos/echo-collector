from fastapi import APIRouter

router = APIRouter(prefix="/echo", tags=["Echo"])


@router.get("/health")
async def echo_health() -> dict[str, str]:
    return {"service": "echo-collector", "status": "ok"}
