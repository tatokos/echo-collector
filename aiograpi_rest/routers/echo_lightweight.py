from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from aiograpi_rest.lightweight_scoring import load_objectives, score_text
from aiograpi_rest.routers.echo import _load_keywords

router = APIRouter(prefix="/echo", tags=["Echo"])


class AnalyzeLightInput(BaseModel):
    text: str = Field(min_length=3, max_length=3000)
    username: str = Field(default="test", max_length=100)


@router.post("/analyze-light")
async def echo_analyze_light(item: AnalyzeLightInput) -> dict[str, Any]:
    result = score_text(item.text, item.username, _load_keywords(), load_objectives())
    return {"text": item.text, **result}
