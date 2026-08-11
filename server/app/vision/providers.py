"""BYO-AI vision provider clients (Anthropic, OpenAI) over raw httpx.

No provider SDKs: fewer dependencies for an OSS project, and both providers
can be tested uniformly with ``httpx.MockTransport``.

KEY SAFETY: the caller's API key is passed per-call and must NEVER be stored,
logged, or placed anywhere it could leak. Keys travel only in request headers
(never the URL) — httpx exception messages include the URL, not headers, so a
raised ``HTTPStatusError`` cannot expose the key.
"""

import base64
from typing import Optional

import httpx

from app.schemas import VisionResult
from app.vision.prompt import build_prompt, parse_vision_json


class ProviderAuthError(Exception):
    pass


class ProviderRateLimited(Exception):
    pass


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


async def analyze_card(front: bytes, front_type: str, back: Optional[tuple[bytes, str]],
                       provider: str, api_key: str, model: str,
                       transport: Optional[httpx.BaseTransport] = None) -> VisionResult:
    if provider not in ("anthropic", "openai"):
        raise ValueError(f"Unsupported provider: {provider}")
    async with httpx.AsyncClient(transport=transport, timeout=60) as http:
        if provider == "anthropic":
            raw = await _call_anthropic(http, front, front_type, back, api_key, model)
        else:
            raw = await _call_openai(http, front, front_type, back, api_key, model)
    return parse_vision_json(raw)


def _raise_for_provider_status(resp: httpx.Response) -> None:
    if resp.status_code in (401, 403):
        raise ProviderAuthError("AI provider rejected the API key")
    if resp.status_code == 429:
        raise ProviderRateLimited("AI provider rate limit hit")
    resp.raise_for_status()


async def _call_anthropic(http: httpx.AsyncClient, front: bytes, front_type: str,
                          back: Optional[tuple[bytes, str]], api_key: str, model: str) -> str:
    content: list[dict] = [{"type": "image",
                            "source": {"type": "base64", "media_type": front_type,
                                       "data": _b64(front)}}]
    if back:
        content.append({"type": "image",
                        "source": {"type": "base64", "media_type": back[1],
                                   "data": _b64(back[0])}})
    content.append({"type": "text", "text": build_prompt()})
    resp = await http.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        json={"model": model, "max_tokens": 2048,
              "messages": [{"role": "user", "content": content}]},
    )
    _raise_for_provider_status(resp)
    return "".join(b.get("text", "") for b in resp.json()["content"] if b.get("type") == "text")


async def _call_openai(http: httpx.AsyncClient, front: bytes, front_type: str,
                       back: Optional[tuple[bytes, str]], api_key: str, model: str) -> str:
    content: list[dict] = [{"type": "image_url",
                            "image_url": {"url": f"data:{front_type};base64,{_b64(front)}"}}]
    if back:
        content.append({"type": "image_url",
                        "image_url": {"url": f"data:{back[1]};base64,{_b64(back[0])}"}})
    content.append({"type": "text", "text": build_prompt()})
    resp = await http.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "max_tokens": 2048,
              "messages": [{"role": "user", "content": content}],
              "response_format": {"type": "json_object"}},
    )
    _raise_for_provider_status(resp)
    return resp.json()["choices"][0]["message"]["content"]
