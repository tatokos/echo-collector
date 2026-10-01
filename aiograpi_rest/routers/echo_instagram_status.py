from typing import Any

from fastapi import APIRouter, Depends

from aiograpi_rest.dependencies import ClientStorage, get_clients
from aiograpi_rest.routers.echo import _supabase_request

router = APIRouter(prefix="/echo/instagram", tags=["Echo"])


def _vault_configured() -> bool:
    value = _supabase_request("POST", "rpc/echo_get_instagram_session", payload={})
    return bool(value.strip()) if isinstance(value, str) else False


@router.get("/status")
async def instagram_status(
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, Any]:
    local_count = len(clients.db.all())
    vault = _vault_configured()
    return {
        "configured": vault,
        "temporary_session": local_count > 0,
        "status": "connected" if vault else ("temporary" if local_count > 0 else "disconnected"),
    }
