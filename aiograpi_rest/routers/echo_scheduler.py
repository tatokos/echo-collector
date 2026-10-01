import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from aiograpi_rest.dependencies import ClientStorage, get_clients
from aiograpi_rest.lightweight_scoring import upsert_posts_lightweight
from aiograpi_rest.routers.echo import (
    _load_keywords,
    _normalize_media,
    _supabase_request,
)

router = APIRouter(prefix="/echo", tags=["Echo"])


def _require_automation(key: str | None) -> None:
    expected = os