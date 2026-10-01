from pathlib import Path

from fastapi.responses import FileResponse

from aiograpi_rest.main import app
from aiograpi_rest.routers import echo, echo_scheduler

app.include_router(echo.router)
app.include_router(echo_scheduler.router)


@app.get("/echo/app", include_in_schema=False)
async def echo_app() -> FileResponse:
    return FileResponse(Path(__file__).with_name("echo_ui.html"))
