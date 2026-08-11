from typing import Annotated, Optional

import httpx
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import scan as scan_module
from app.config import get_settings
from app.schemas import ScanResponse
from app.vision.prompt import VisionParseError
from app.vision.providers import ProviderAuthError, ProviderRateLimited

app = FastAPI(title="Card Scanner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # public, keyless API surface; the AI key is the user's own
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/scan", response_model=ScanResponse)
async def scan(
    front: Annotated[UploadFile, File()],
    x_ai_provider: Annotated[str, Header()],
    x_ai_key: Annotated[str, Header()],
    x_ai_model: Annotated[Optional[str], Header()] = None,
    back: Annotated[Optional[UploadFile], File()] = None,
    asking_price: Annotated[Optional[float], Form()] = None,
):
    settings = get_settings()
    if x_ai_provider not in ("anthropic", "openai"):
        raise HTTPException(422, "X-AI-Provider must be 'anthropic' or 'openai'")
    if asking_price is not None and asking_price < 0:
        raise HTTPException(422, "asking_price must be >= 0")
    model = x_ai_model or (settings.anthropic_default_model if x_ai_provider == "anthropic"
                           else settings.openai_default_model)
    front_bytes = await front.read()
    back_tuple = None
    if back is not None:
        back_tuple = (await back.read(), back.content_type or "image/jpeg")
    # Only vision-path errors surface here; eBay failures become a partial
    # result (comps_error) inside perform_scan.
    try:
        return await scan_module.perform_scan(
            front_bytes, front.content_type or "image/jpeg", back_tuple,
            provider=x_ai_provider, api_key=x_ai_key, model=model,
            asking_price=asking_price)
    except ProviderAuthError:
        raise HTTPException(401, "Your AI provider rejected the API key. Check it in Settings.")
    except ProviderRateLimited:
        raise HTTPException(429, "Your AI provider is rate limiting. Wait a moment and retry.")
    except VisionParseError:
        raise HTTPException(502, "The AI returned an unreadable analysis. Try scanning again.")
    except httpx.HTTPStatusError:
        raise HTTPException(502, "Your AI provider returned an error. Try again.")
    except httpx.TransportError:
        raise HTTPException(502, "Could not reach your AI provider. Check your connection.")
