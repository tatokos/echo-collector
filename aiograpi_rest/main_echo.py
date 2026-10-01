from pathlib import Path

from fastapi.responses import FileResponse, HTMLResponse

from aiograpi_rest.main import app
from aiograpi_rest.routers import echo, echo_instagram_status, echo_lightweight, echo_objectives, echo_scheduler

app.include_router(echo.router)
app.include_router(echo_objectives.router)
app.include_router(echo_scheduler.router)
app.include_router(echo_lightweight.router)
app.include_router(echo_instagram_status.router)

_NO_CACHE = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


@app.get("/echo/app", include_in_schema=False)
async def echo_app() -> HTMLResponse:
    html = Path(__file__).with_name("echo_ui.html").read_text(encoding="utf-8")
    scripts = '<script src="/echo/instagram-ui.js"></script><script src="/echo/pretest-ui.js"></script>'
    html = html.replace("</body>", f"{scripts}</body>")
    return HTMLResponse(html, headers=_NO_CACHE)


@app.get("/echo/instagram-ui.js", include_in_schema=False)
async def echo_instagram_ui() -> FileResponse:
    return FileResponse(
        Path(__file__).with_name("echo_instagram_ui.js"),
        media_type="application/javascript",
        headers=_NO_CACHE,
    )


@app.get("/echo/pretest-ui.js", include_in_schema=False)
async def echo_pretest_ui() -> FileResponse:
    return FileResponse(
        Path(__file__).with_name("echo_pretest_ui.js"),
        media_type="application/javascript",
        headers=_NO_CACHE,
    )
