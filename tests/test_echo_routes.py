from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from aiograpi_rest.dependencies import get_clients
from aiograpi_rest.main_echo import app
from aiograpi_rest.routers.echo import _score_post


class FakeEchoClient:
    def __init__(self):
        self.calls = []

    async def user_info_by_username_v1(self, username):
        self.calls.append(("user_info_by_username_v1", username))
        return SimpleNamespace(pk="12345")

    async def user_medias_paginated_v1(self, user_id, amount=0, end_cursor=""):
        self.calls.append(("user_medias_paginated_v1", user_id, amount, end_cursor))
        media = SimpleNamespace(
            pk=999,
            code="ABC123",
            taken_at=datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc),
            media_type=1,
            product_type="feed",
            user=SimpleNamespace(username="example"),
            caption_text="Test caption",
            thumbnail_url="https://example.com/thumb.jpg",
            video_url=None,
            like_count=10,
            comment_count=2,
        )
        return [media], "next-cursor"


class FakeStorage:
    def __init__(self):
        self.client = FakeEchoClient()

    async def get(self, sessionid):
        return self.client

    def close(self):
        pass


@pytest.fixture
def storage():
    fake = FakeStorage()
    app.dependency_overrides[get_clients] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_echo_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/echo/health")
    assert response.status_code == 200
    assert response.json() == {"service": "echo-collector", "status": "ok"}


@pytest.mark.asyncio
async def test_echo_preview_returns_normalized_posts(storage):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/echo/preview",
            params={"username": "@example", "limit": 5},
            headers={"X-Session-ID": "sid"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "instagram"
    assert payload["username"] == "example"
    assert payload["count"] == 1
    assert payload["next_cursor"] == "next-cursor"
    assert payload["posts"][0] == {
        "instagram_id": "999",
        "code": "ABC123",
        "permalink": "https://www.instagram.com/p/ABC123/",
        "username": "example",
        "caption": "Test caption",
        "published_at": "2026-09-28T12:00:00+00:00",
        "media_type": 1,
        "product_type": "feed",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "video_url": None,
        "like_count": 10,
        "comment_count": 2,
    }
    assert ("user_info_by_username_v1", "example") in storage.client.calls
    assert ("user_medias_paginated_v1", "12345", 5, "") in storage.client.calls


def test_score_post_uses_configured_weights():
    post = {"username": "example", "caption": "A cruise in Naples"}
    keywords = [
        {"keyword": "cruise", "weight": 35},
        {"keyword": "Naples", "weight": 20},
    ]

    score, relevance, reason = _score_post(post, keywords)

    assert score == 55
    assert relevance == "MEDIA"
    assert "cruise" in reason
    assert "Naples" in reason
