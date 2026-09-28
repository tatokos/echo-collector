from aiograpi_rest.main import app
from aiograpi_rest.routers import echo

app.include_router(echo.router)
