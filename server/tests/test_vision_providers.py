import json

import httpx
import pytest

from app.vision.prompt import VisionParseError
from app.vision.providers import ProviderAuthError, ProviderRateLimited, analyze_card

VISION_JSON = '{"photo_ok": false, "photo_issue": "blurry"}'


def anthropic_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.anthropic.com"
        assert request.headers["x-api-key"] == "user-key"
        return httpx.Response(200, json={"content": [{"type": "text", "text": VISION_JSON}]})
    return httpx.MockTransport(handler)


def openai_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer user-key"
        return httpx.Response(200, json={"choices": [{"message": {"content": VISION_JSON}}]})
    return httpx.MockTransport(handler)


async def test_anthropic_flow():
    r = await analyze_card(b"fakejpg", "image/jpeg", None, provider="anthropic",
                           api_key="user-key", model="claude-sonnet-5",
                           transport=anthropic_transport())
    assert r.photo_ok is False


async def test_openai_flow():
    r = await analyze_card(b"fakejpg", "image/jpeg", None, provider="openai",
                           api_key="user-key", model="gpt-5.1",
                           transport=openai_transport())
    assert r.photo_ok is False


async def test_bad_key_raises_auth_error():
    transport = httpx.MockTransport(lambda req: httpx.Response(401, json={}))
    with pytest.raises(ProviderAuthError):
        await analyze_card(b"x", "image/jpeg", None, provider="anthropic",
                           api_key="bad", model="claude-sonnet-5", transport=transport)


async def test_unknown_provider_rejected():
    with pytest.raises(ValueError):
        await analyze_card(b"x", "image/jpeg", None, provider="grok",
                           api_key="k", model="m", transport=None)


async def test_anthropic_back_image_included():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"content": [{"type": "text", "text": VISION_JSON}]})

    await analyze_card(b"front", "image/jpeg", (b"back", "image/png"),
                       provider="anthropic", api_key="user-key", model="claude-sonnet-5",
                       transport=httpx.MockTransport(handler))
    content = seen["payload"]["messages"][0]["content"]
    images = [b for b in content if b["type"] == "image"]
    assert len(images) == 2
    assert images[1]["source"]["media_type"] == "image/png"


async def test_rate_limit_raises_provider_rate_limited():
    transport = httpx.MockTransport(lambda req: httpx.Response(429, json={}))
    with pytest.raises(ProviderRateLimited):
        await analyze_card(b"x", "image/jpeg", None, provider="openai",
                           api_key="k", model="gpt-5.1", transport=transport)


async def test_server_error_propagates_as_http_status_error():
    transport = httpx.MockTransport(lambda req: httpx.Response(500, json={}))
    with pytest.raises(httpx.HTTPStatusError):
        await analyze_card(b"x", "image/jpeg", None, provider="anthropic",
                           api_key="k", model="claude-sonnet-5", transport=transport)


async def test_garbage_text_raises_vision_parse_error():
    transport = httpx.MockTransport(lambda req: httpx.Response(
        200, json={"content": [{"type": "text", "text": "sorry, I cannot help with that"}]}))
    with pytest.raises(VisionParseError):
        await analyze_card(b"x", "image/jpeg", None, provider="anthropic",
                           api_key="k", model="claude-sonnet-5", transport=transport)


async def test_key_never_in_url():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "user-key" not in str(request.url)
        return httpx.Response(200, json={"choices": [{"message": {"content": VISION_JSON}}]})

    await analyze_card(b"x", "image/jpeg", None, provider="openai",
                       api_key="user-key", model="gpt-5.1",
                       transport=httpx.MockTransport(handler))
