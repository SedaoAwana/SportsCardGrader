"""Scan orchestration: vision -> comps -> verdict, with partial results.

Vision-path errors propagate to the endpoint (mapped to HTTP statuses);
eBay/comps errors are swallowed into ScanResponse.comps_error so the user
still gets the vision analysis they paid an AI call for.
"""
from typing import Optional

from app.comps import summarize
from app.config import get_settings
from app.ebay import EbayClient
from app.schemas import CompListing, ScanResponse, VisionResult
from app.verdict import decide
from app.vision.providers import analyze_card

_ebay_client: Optional[EbayClient] = None


async def run_vision(front: bytes, front_type: str, back: Optional[tuple[bytes, str]],
                     provider: str, api_key: str, model: str) -> VisionResult:
    return await analyze_card(front, front_type, back, provider=provider,
                              api_key=api_key, model=model)


async def search_comps(query: str) -> list[CompListing]:
    global _ebay_client
    settings = get_settings()
    if not settings.ebay_configured:
        raise RuntimeError("eBay credentials not configured on this server")
    if _ebay_client is None:
        _ebay_client = EbayClient(settings.ebay_client_id, settings.ebay_client_secret,
                                  settings.ebay_env)
    return await _ebay_client.search(query)


async def perform_scan(front: bytes, front_type: str, back: Optional[tuple[bytes, str]],
                       provider: str, api_key: str, model: str,
                       asking_price: Optional[float]) -> ScanResponse:
    vision = await run_vision(front, front_type, back, provider, api_key, model)
    if not vision.photo_ok or vision.identity is None or vision.condition is None:
        return ScanResponse(vision=vision)

    try:
        listings = await search_comps(vision.identity.search_string)
    except Exception as e:
        return ScanResponse(vision=vision, comps_error=str(e))

    comps = summarize(listings, source="active_listings")
    verdict = decide(comps, vision.condition, asking_price, vision.identity.confidence)
    return ScanResponse(vision=vision, comps=comps, verdict=verdict)
