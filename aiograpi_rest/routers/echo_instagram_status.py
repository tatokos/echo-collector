from fastapi import APIRouter, Depends

from aiograpi_rest.dependencies import ClientStorage, get_clients

router = APIRouter(prefix="/echo/instagram", tags=["Echo"])


@router.get("/status")
async def instagram_status(
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, object]:
    configured = clients.has_login()
    return {
        "configured": configured,
        "status": "connected" if configured else "disconnected",
    }
