import base64
import time
from typing import Optional

import httpx
from pydantic import ValidationError

from app.comps import is_graded
from app.schemas import CompListing

_BASES = {"production": "https://api.ebay.com", "sandbox": "https://api.sandbox.ebay.com"}
SPORTS_CARDS_CATEGORY = "212"


class EbayClient:
    def __init__(self, client_id: str, client_secret: str, env: str = "production",
                 transport: Optional[httpx.BaseTransport] = None):
        self._base = _BASES[env]
        self._basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        self._token: Optional[str] = None
        self._token_expiry = 0.0
        self._http = httpx.AsyncClient(base_url=self._base, transport=transport, timeout=15)

    async def _get_token(self) -> str:
        if self._token and time.monotonic() < self._token_expiry - 60:
            return self._token
        resp = await self._http.post(
            "/identity/v1/oauth2/token",
            headers={"Authorization": f"Basic {self._basic}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials",
                  "scope": "https://api.ebay.com/oauth/api_scope"},
        )
        resp.raise_for_status()
        payload = resp.json()
        self._token = payload["access_token"]
        self._token_expiry = time.monotonic() + payload.get("expires_in", 7200)
        return self._token

    async def search(self, query: str, limit: int = 50) -> list[CompListing]:
        token = await self._get_token()
        resp = await self._http.get(
            "/buy/browse/v1/item_summary/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "category_ids": SPORTS_CARDS_CATEGORY, "limit": limit},
        )
        resp.raise_for_status()
        items = resp.json().get("itemSummaries", [])
        listings: list[CompListing] = []
        for it in items:
            price = it.get("price", {}).get("value")
            if price is None:
                continue
            title = it.get("title", "")
            # A single malformed item (negative or non-numeric price) should be
            # skipped, not fail the whole search.
            try:
                listings.append(CompListing(title=title, price=float(price),
                                            graded=is_graded(title), url=it.get("itemWebUrl")))
            except (ValueError, TypeError, ValidationError):
                continue
        return listings
