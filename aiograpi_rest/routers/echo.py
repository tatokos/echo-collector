from typing import Any

from fastapi import APIRouter, Depends, Query

from aiograpi_rest.dependencies import ClientStorage, get_clients, get_sessionid

router = APIRouter(prefix="/echo", tags=["Echo"])


def _as_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _normalize_media(media: Any, fallback_username: str) -> dict[str, Any]:
    code = _as_string(getattr(media, "code", None))
    taken_at = getattr(media, "taken_at", None)
    author = getattr(media, "user", None)
    username = getattr(author, "username", None) or fallback_username

    return {
        "instagram_id": _as_string(getattr(media, "pk", None)),
        "code": code,
        "permalink": f"https://www.instagram.com/p/{code}/" if code else None,
        "username": username,
        "caption": getattr(media, "caption_text", "") or "",
        "taken_at": taken_at.isoformat() if hasattr(taken_at, "isoformat") else _as_string(taken_at),
        "media_type": getattr(media, "media_type", None),
        "product_type": getattr(media, "product_type", None),
        "thumbnail_url": _as_string(getattr(media, "thumbnail_url", None)),
        "video_url": _as_string(getattr(media, "video_url", None)),
        "like_count": getattr(media, "like_count", None),
        "comment_count": getattr(media, "comment_count", None),
    }


@router.get("/health")
async def echo_health() -> dict[str, str]:
    return {"service": "echo-collector", "status": "ok"}


@router.get("/preview")
async def echo_preview(
    username: str = Query(..., min_length=1, description="Public Instagram username to inspect."),
    limit: int = Query(5, ge=1, le=20),
    sessionid: str = Depends(get_sessionid),
    clients: ClientStorage = Depends(get_clients),
) -> dict[str, Any]:
    """Return a normalized preview of a public Instagram profile's latest posts."""
    clean_username = username.strip().lstrip("@")
    cl = await clients.get(sessionid)
    user = await cl.user_info_by_username_v1(clean_username)
    items, next_cursor = await cl.user_medias_paginated_v1(str(user.pk), limit, "")

    posts = [_normalize_media(media, clean_username) for media in items]
    return {
        "source": "instagram",
        "username": clean_username,
        "count": len(posts),
        "posts": posts,
        "next_cursor": next_cursor or "",
    }
