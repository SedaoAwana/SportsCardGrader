"""Scan orchestration: vision -> comps -> verdict, with partial results.

Vision-path errors propagate to the endpoint (mapped to HTTP statuses);
pricing/comps errors are swallowed into ScanResponse.comps_error so the user
still gets the vision analysis they paid an AI call for.
"""
from typing import Optional

from app.comps import summarize
from app.config import get_settings
from app.pricing import PricingSource, get_pricing_source
from app.schemas import CompListing, ScanResponse, VisionResult
from app.verdict import decide
from app.vision.providers import analyze_card

_pricing_source: Optional[PricingSource] = None


def _get_pricing_source() -> PricingSource:
    global _pricing_source
    if _pricing_source is None:
        _pricing_source = get_pricing_source(get_settings())
    return _pricing_source


async def run_vision(front: bytes, front_type: str, back: Optional[tuple[bytes, str]],
                     provider: str, api_key: str, model: str) -> VisionResult:
    return await analyze_card(front, front_type, back, provider=provider,
                              api_key=api_key, model=model)


async def search_comps(query: str) -> list[CompListing]:
    return await _get_pricing_source().search(query)


async def perform_scan(front: bytes, front_type: str, back: Optional[tuple[bytes, str]],
                       provider: str, api_key: str, model: str,
                       asking_price: Optional[float]) -> ScanResponse:
    vision = await run_vision(front, front_type, back, provider, api_key, model)
    if not vision.photo_ok or vision.identity is None or vision.condition is None:
        return ScanResponse(vision=vision)

    try:
        # Resolved inside the try so a misconfigured PRICING_SOURCE degrades to
        # a self-diagnosing comps_error instead of a 500.
        source_type = _get_pricing_source().source_type
        listings = await search_comps(vision.identity.search_string)
    except Exception as e:
        return ScanResponse(vision=vision, comps_error=str(e))

    comps = summarize(listings, source=source_type)
    verdict = decide(comps, vision.condition, asking_price, vision.identity.confidence,
                     authenticity=vision.authenticity)
    return ScanResponse(vision=vision, comps=comps, verdict=verdict)
