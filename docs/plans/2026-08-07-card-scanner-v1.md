# Card Scanner v1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild SportsCardGrader as an open-source, mobile-first card scanner: photo → identity + grade range + authenticity red flags + eBay-priced verdict (undervalued / fair / overpriced).

**Architecture:** Stateless FastAPI server (`server/`) orchestrates three stages per scan — vision analysis on the *user's own* AI key (BYO-AI, passed in headers, never stored), eBay comps on the *deployer's* credentials (env vars), and a pure-math verdict engine. Vite/React/TS PWA (`web/`) captures photos, stores the AI key and scan history in `localStorage` only. Every degraded path returns partial results.

**Tech Stack:** Python 3.12, FastAPI, httpx, pydantic v2, pytest · Vite, React 18, TypeScript, vitest · No database, no queue, no accounts.

**Design doc:** `docs/plans/2026-08-07-card-scanner-design.md` (read it first).

---

## Conventions

- Server code lives under `server/`, run commands from `server/` with `.venv` active unless stated.
- Web code lives under `web/`, run commands from `web/`.
- Commit after every task (each task ends with a commit step).
- The user's AI key arrives in headers `X-AI-Provider` (`anthropic`|`openai`) and `X-AI-Key`, optional `X-AI-Model`. It must never appear in logs, error messages, or persisted state.

---

### Task 1: Repo cleanup + MIT license

Delete the legacy implementation (code review found the CV pipeline measured the wrong things — see design doc). Keep `sample_images/` (test fixtures) and `docs/`.

**Files:**
- Delete: `sports_card_grader/`, `api_server.py`, `sports_card_cli.py`, `examples.py`, `setup.py`, `test_demo.py`, `test_card.jpg`, `requirements.txt`, `frontend/`
- Create: `LICENSE`

**Step 1: Delete legacy code**

```bash
git rm -r sports_card_grader api_server.py sports_card_cli.py examples.py setup.py test_demo.py test_card.jpg requirements.txt frontend
```

**Step 2: Add MIT license**

Create `LICENSE` with the standard MIT text, copyright line:

```
Copyright (c) 2026 Calvin Sedao
```

**Step 3: Verify repo state**

Run: `git status --short` — expected: deletions staged, `LICENSE` untracked. `ls` should show `LICENSE README.md docs sample_images`.

**Step 4: Commit**

```bash
git add LICENSE && git commit -m "chore: remove legacy implementation, add MIT license"
```

---

### Task 2: Server scaffold + health endpoint

**Files:**
- Create: `server/pyproject.toml`, `server/app/__init__.py`, `server/app/main.py`, `server/tests/__init__.py`, `server/tests/test_health.py`

**Step 1: Scaffold**

Create `server/pyproject.toml`:

```toml
[project]
name = "card-scanner-server"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "httpx>=0.27",
    "pydantic>=2.8",
    "pydantic-settings>=2.4",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.24"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

```bash
cd server && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

**Step 2: Write the failing test**

`server/tests/test_health.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```

**Step 3: Run it — verify it fails**

Run: `pytest tests/test_health.py -v` — expected: FAIL (`ModuleNotFoundError: app`).

**Step 4: Minimal implementation**

`server/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Card Scanner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # public, keyless API surface; the AI key is the user's own
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

Create empty `server/app/__init__.py` and `server/tests/__init__.py`.

**Step 5: Run test — verify PASS, then commit**

Run: `pytest -v` — expected: 1 passed.

```bash
git add server && git commit -m "feat(server): FastAPI scaffold with health endpoint"
```

---

### Task 3: PSA grade-scale reference data

Carried over from the old `grading_system.py` — the one piece worth keeping. Used to ground the vision prompt and UI copy.

**Files:**
- Create: `server/app/data/__init__.py`, `server/app/data/psa_scale.py`
- Test: `server/tests/test_psa_scale.py`

**Step 1: Write the failing test**

```python
from app.data.psa_scale import PSA_SCALE

def test_scale_has_ten_grades():
    assert set(PSA_SCALE) == {str(n) for n in range(1, 11)}

def test_grade_entries_complete():
    for grade, entry in PSA_SCALE.items():
        assert entry["label"]
        assert entry["description"]
```

**Step 2: Run — verify FAIL** (`ModuleNotFoundError`)

**Step 3: Implement**

Create `server/app/data/psa_scale.py` with `PSA_SCALE: dict` — copy the `GRADE_SCALE` dict verbatim from the old repo's `sports_card_grader/grading_system.py` (grades "1"–"10" with `label`, `description`, `centering_tolerance`; drop the `min` scoring thresholds — they belonged to the fake scorer). Git history has it: `git show main:sports_card_grader/grading_system.py`.

**Step 4: Run — verify PASS. Step 5: Commit**

```bash
git add server/app/data server/tests/test_psa_scale.py && git commit -m "feat(server): PSA grade scale reference data"
```

---

### Task 4: Result schemas

The shared vocabulary for the whole pipeline. No logic — just pydantic models mirrored later in `web/src/types.ts`.

**Files:**
- Create: `server/app/schemas.py`
- Test: `server/tests/test_schemas.py`

**Step 1: Write the failing test**

```python
import pytest
from pydantic import ValidationError
from app.schemas import Identity, Condition, VisionResult, Verdict

def test_identity_confidence_bounds():
    with pytest.raises(ValidationError):
        Identity(player="Luka Doncic", year="2018", set_name="Prizm",
                 search_string="x", confidence=1.5)

def test_condition_rejects_inverted_range():
    with pytest.raises(ValidationError):
        Condition(observations=[], grade_low=8, grade_high=6)

def test_vision_result_photo_rejected_needs_no_identity():
    r = VisionResult(photo_ok=False, photo_issue="too blurry")
    assert r.identity is None
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`server/app/schemas.py`:

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

class Identity(BaseModel):
    player: str
    year: str
    set_name: str
    card_number: Optional[str] = None
    variant: Optional[str] = None
    search_string: str
    confidence: float = Field(ge=0, le=1)

class AreaObservation(BaseModel):
    area: Literal["corners", "edges", "surface", "centering"]
    severity: Literal["none", "minor", "moderate", "heavy"]
    note: str

class Condition(BaseModel):
    observations: list[AreaObservation]
    grade_low: int = Field(ge=1, le=10)
    grade_high: int = Field(ge=1, le=10)

    @model_validator(mode="after")
    def range_ordered(self):
        if self.grade_low > self.grade_high:
            raise ValueError("grade_low must be <= grade_high")
        return self

class Authenticity(BaseModel):
    red_flags: list[str]
    risk: Literal["low", "caution", "high"]

class VisionResult(BaseModel):
    photo_ok: bool
    photo_issue: Optional[str] = None
    identity: Optional[Identity] = None
    condition: Optional[Condition] = None
    authenticity: Optional[Authenticity] = None
    ai_value_note: Optional[str] = None  # model's rough value memory; fallback when comps are empty

class CompListing(BaseModel):
    title: str
    price: float
    graded: bool
    grade_label: Optional[str] = None
    url: Optional[str] = None

class CompsSummary(BaseModel):
    source: Literal["active_listings", "sold"]
    raw_count: int
    raw_low: Optional[float] = None
    raw_median: Optional[float] = None
    graded_count: int
    graded_low: Optional[float] = None
    graded_median: Optional[float] = None

class Verdict(BaseModel):
    value_low: Optional[float] = None
    value_high: Optional[float] = None
    verdict: Literal["undervalued", "fair", "overpriced", "no_ask", "not_enough_data"]
    reasoning: str

class ScanResponse(BaseModel):
    vision: VisionResult
    comps: Optional[CompsSummary] = None
    comps_error: Optional[str] = None
    verdict: Optional[Verdict] = None
```

**Step 4: Run — verify PASS. Step 5: Commit**

```bash
git add server/app/schemas.py server/tests/test_schemas.py && git commit -m "feat(server): scan result schemas"
```

---

### Task 5: Comps summarizer (pure function)

Turns raw eBay listings into the `CompsSummary` buckets. Graded = title mentions a grading company + numeric grade.

**Files:**
- Create: `server/app/comps.py`
- Test: `server/tests/test_comps.py`

**Step 1: Write the failing tests**

```python
from app.comps import summarize, is_graded
from app.schemas import CompListing

def L(title, price):
    return CompListing(title=title, price=price, graded=is_graded(title))

def test_is_graded_detects_companies():
    assert is_graded("2018 Prizm Luka Doncic PSA 10")
    assert is_graded("Luka RC BGS 9.5 GEM")
    assert not is_graded("2018 Prizm Luka Doncic RC #280")

def test_summarize_buckets_and_medians():
    listings = [L("Luka raw", 40), L("Luka raw RC", 60), L("Luka RC nice", 80),
                L("Luka PSA 10", 400), L("Luka PSA 9", 150)]
    s = summarize(listings, source="active_listings")
    assert (s.raw_count, s.raw_low, s.raw_median) == (3, 40, 60)
    assert (s.graded_count, s.graded_low) == (2, 150)

def test_summarize_empty():
    s = summarize([], source="active_listings")
    assert s.raw_count == 0 and s.raw_low is None
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`server/app/comps.py`:

```python
import re
import statistics
from app.schemas import CompListing, CompsSummary

_GRADED_RE = re.compile(r"\b(PSA|BGS|SGC|CGC)\s*\.?\s*(10|[1-9](?:\.5)?)\b", re.I)

def is_graded(title: str) -> bool:
    return bool(_GRADED_RE.search(title))

def summarize(listings: list[CompListing], source: str) -> CompsSummary:
    raw = sorted(l.price for l in listings if not l.graded)
    graded = sorted(l.price for l in listings if l.graded)
    return CompsSummary(
        source=source,
        raw_count=len(raw),
        raw_low=raw[0] if raw else None,
        raw_median=statistics.median(raw) if raw else None,
        graded_count=len(graded),
        graded_low=graded[0] if graded else None,
        graded_median=statistics.median(graded) if graded else None,
    )
```

**Step 4: Run — verify PASS. Step 5: Commit**

```bash
git add server/app/comps.py server/tests/test_comps.py && git commit -m "feat(server): comps summarizer"
```

---

### Task 6: Verdict engine (pure functions — test hard)

The money logic. Value range comes from the **raw** bucket (v1 assumes the card in hand is raw); graded upside is mentioned in reasoning only. Comps sufficiency is judged on the raw bucket alone (raw_count >= MIN_COMPS) — graded comps cannot rescue a thin raw bucket, since the value range is priced entirely from raw listings. Thresholds: undervalued if ask ≤ 70% of value_low, overpriced if ask ≥ 120% of value_high.

**Files:**
- Create: `server/app/verdict.py`
- Test: `server/tests/test_verdict.py`

**Step 1: Write the failing tests**

```python
from app.verdict import decide
from app.schemas import CompsSummary, Condition

def comps(**kw):
    base = dict(source="active_listings", raw_count=5, raw_low=60.0, raw_median=90.0,
                graded_count=0, graded_low=None, graded_median=None)
    base.update(kw)
    return CompsSummary(**base)

def cond(lo=6, hi=8):
    return Condition(observations=[], grade_low=lo, grade_high=hi)

def test_undervalued():
    v = decide(comps(), cond(), asking_price=30.0, identity_confidence=0.9)
    assert v.verdict == "undervalued"
    assert v.value_low == 60.0 and v.value_high == 90.0

def test_fair():
    assert decide(comps(), cond(), 75.0, 0.9).verdict == "fair"

def test_overpriced():
    assert decide(comps(), cond(), 150.0, 0.9).verdict == "overpriced"

def test_no_ask_returns_value_only():
    v = decide(comps(), cond(), None, 0.9)
    assert v.verdict == "no_ask" and v.value_low == 60.0

def test_low_identity_confidence_downgrades():
    assert decide(comps(), cond(), 30.0, 0.4).verdict == "not_enough_data"

def test_thin_comps_downgrades():
    thin = comps(raw_count=1, graded_count=1)
    assert decide(thin, cond(), 30.0, 0.9).verdict == "not_enough_data"

def test_graded_upside_mentioned_when_high_grade_possible():
    c = comps(graded_count=3, graded_low=150.0, graded_median=400.0)
    v = decide(c, cond(lo=8, hi=9), 30.0, 0.9)
    assert "graded" in v.reasoning.lower()
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`server/app/verdict.py`:

```python
from typing import Optional
from app.schemas import CompsSummary, Condition, Verdict

MIN_CONFIDENCE = 0.5
MIN_COMPS = 3
UNDERVALUED_RATIO = 0.7
OVERPRICED_RATIO = 1.2

def decide(comps: CompsSummary, condition: Condition,
           asking_price: Optional[float], identity_confidence: float) -> Verdict:
    if identity_confidence < MIN_CONFIDENCE:
        return Verdict(verdict="not_enough_data",
                       reasoning="Card identification confidence is too low to price reliably. Try a clearer photo.")
    if comps.raw_count < MIN_COMPS or comps.raw_low is None or comps.raw_median is None:
        return Verdict(verdict="not_enough_data",
                       reasoning="Too few comparable raw listings found to establish a value.")

    value_low, value_high = comps.raw_low, comps.raw_median
    src = "sold prices" if comps.source == "sold" else "current asking prices"
    reasoning = f"Raw copies range ${value_low:.0f}–${value_high:.0f} based on {comps.raw_count} {src}."
    if condition.grade_high >= 8 and comps.graded_count and comps.graded_low:
        reasoning += (f" If it grades near the top of its {condition.grade_low}–{condition.grade_high} range, "
                      f"graded copies start around ${comps.graded_low:.0f}.")

    if asking_price is None:
        return Verdict(value_low=value_low, value_high=value_high, verdict="no_ask", reasoning=reasoning)

    if asking_price <= value_low * UNDERVALUED_RATIO:
        label, tail = "undervalued", f" The ${asking_price:.0f} ask is well below the low end."
    elif asking_price >= value_high * OVERPRICED_RATIO:
        label, tail = "overpriced", f" The ${asking_price:.0f} ask is above the typical range."
    else:
        label, tail = "fair", f" The ${asking_price:.0f} ask sits within the typical range."
    return Verdict(value_low=value_low, value_high=value_high, verdict=label, reasoning=reasoning + tail)
```

**Step 4: Run — verify PASS (all 7). Step 5: Commit**

```bash
git add server/app/verdict.py server/tests/test_verdict.py && git commit -m "feat(server): verdict engine"
```

---

### Task 7: Settings/config

**Files:**
- Create: `server/app/config.py`, `.env.example` (repo root)
- Test: `server/tests/test_config.py`

**Step 1: Write the failing test**

```python
from app.config import Settings

def test_defaults_allow_missing_ebay(monkeypatch):
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    s = Settings(_env_file=None)
    assert s.ebay_configured is False

def test_ebay_configured(monkeypatch):
    s = Settings(_env_file=None, ebay_client_id="x", ebay_client_secret="y")
    assert s.ebay_configured is True
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`server/app/config.py`:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_env: str = "production"  # or "sandbox"
    anthropic_default_model: str = "claude-sonnet-5"
    openai_default_model: str = "gpt-5.1"

    model_config = {"env_file": ".env"}

    @property
    def ebay_configured(self) -> bool:
        return bool(self.ebay_client_id and self.ebay_client_secret)

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Create `.env.example` at repo root:

```bash
# eBay developer credentials (free): https://developer.ebay.com — used for price comps.
# The app runs without them; scans just won't include market prices.
EBAY_CLIENT_ID=
EBAY_CLIENT_SECRET=
EBAY_ENV=production
```

**Step 4: Run — verify PASS. Step 5: Commit**

```bash
git add server/app/config.py server/tests/test_config.py .env.example && git commit -m "feat(server): settings via env vars"
```

---

### Task 8: eBay client

Client-credentials OAuth + Browse API search, category 212 (sports trading cards). Tested with `httpx.MockTransport` — no live calls in CI.

**Files:**
- Create: `server/app/ebay.py`
- Test: `server/tests/test_ebay.py`

**Step 1: Write the failing tests**

```python
import httpx
import pytest
from app.ebay import EbayClient

def make_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/identity/v1/oauth2/token":
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 7200})
        if request.url.path == "/buy/browse/v1/item_summary/search":
            assert request.headers["Authorization"] == "Bearer tok"
            return httpx.Response(200, json={"itemSummaries": [
                {"title": "Luka PSA 10", "price": {"value": "400.00"},
                 "itemWebUrl": "https://ebay.com/itm/1"},
                {"title": "Luka raw RC", "price": {"value": "60.00"},
                 "itemWebUrl": "https://ebay.com/itm/2"},
            ]})
        return httpx.Response(404)
    return httpx.MockTransport(handler)

async def test_search_returns_listings():
    client = EbayClient("id", "secret", "production", transport=make_transport())
    listings = await client.search("2018 Prizm Luka Doncic")
    assert len(listings) == 2
    assert listings[0].graded and listings[0].price == 400.0
    assert not listings[1].graded

async def test_search_raises_on_auth_failure():
    def handler(request):
        return httpx.Response(401, json={"error": "invalid_client"})
    client = EbayClient("id", "bad", "production", transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        await client.search("anything")
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`server/app/ebay.py`:

```python
import base64
import time
from typing import Optional
import httpx
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
        listings = []
        for it in items:
            price = it.get("price", {}).get("value")
            if price is None:
                continue
            title = it.get("title", "")
            listings.append(CompListing(title=title, price=float(price),
                                        graded=is_graded(title), url=it.get("itemWebUrl")))
        return listings
```

**Step 4: Run — verify PASS. Step 5: Commit**

```bash
git add server/app/ebay.py server/tests/test_ebay.py && git commit -m "feat(server): eBay Browse API client"
```

---

### Task 9: Vision prompt + response parsing

One module owns the prompt text and the strict parsing of the model's JSON back into `VisionResult`.

**Files:**
- Create: `server/app/vision/__init__.py`, `server/app/vision/prompt.py`
- Test: `server/tests/test_vision_prompt.py`

**Step 1: Write the failing tests**

```python
import pytest
from app.vision.prompt import build_prompt, parse_vision_json, VisionParseError

def test_prompt_mentions_psa_and_json():
    p = build_prompt()
    assert "PSA" in p and "JSON" in p and "photo_ok" in p

def test_parse_strips_code_fences():
    raw = '```json\n{"photo_ok": false, "photo_issue": "blurry"}\n```'
    r = parse_vision_json(raw)
    assert r.photo_ok is False

def test_parse_full_result():
    raw = ('{"photo_ok": true, "identity": {"player": "Luka Doncic", "year": "2018", '
           '"set_name": "Panini Prizm", "card_number": "280", "variant": null, '
           '"search_string": "2018 Panini Prizm Luka Doncic #280", "confidence": 0.92}, '
           '"condition": {"observations": [{"area": "corners", "severity": "minor", '
           '"note": "slight fray top-left"}], "grade_low": 6, "grade_high": 8}, '
           '"authenticity": {"red_flags": [], "risk": "low"}, "ai_value_note": null}')
    r = parse_vision_json(raw)
    assert r.identity.player == "Luka Doncic"
    assert r.condition.grade_high == 8

def test_parse_garbage_raises():
    with pytest.raises(VisionParseError):
        parse_vision_json("I think this is a nice card!")
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`server/app/vision/prompt.py`:

```python
import json
import re
from pydantic import ValidationError
from app.data.psa_scale import PSA_SCALE
from app.schemas import VisionResult

class VisionParseError(Exception):
    pass

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)

def build_prompt() -> str:
    scale = "\n".join(f"PSA {g}: {e['label']} — {e['description']}"
                      for g, e in sorted(PSA_SCALE.items(), key=lambda kv: int(kv[0]), reverse=True))
    return f"""You are analyzing photos of a sports trading card for a collector deciding whether to buy it.

Respond with ONLY a JSON object, no prose, matching exactly this shape:
{{
  "photo_ok": bool,            // false if too blurry/glared/cropped to judge
  "photo_issue": str|null,     // if photo_ok is false: what to fix when retaking
  "identity": {{"player": str, "year": str, "set_name": str, "card_number": str|null,
               "variant": str|null, "search_string": str, "confidence": float 0-1}} | null,
  "condition": {{"observations": [{{"area": "corners"|"edges"|"surface"|"centering",
                "severity": "none"|"minor"|"moderate"|"heavy", "note": str}}],
                "grade_low": int 1-10, "grade_high": int 1-10}} | null,
  "authenticity": {{"red_flags": [str], "risk": "low"|"caution"|"high"}} | null,
  "ai_value_note": str|null    // rough market value from your knowledge, one sentence, or null
}}

Rules:
- "search_string" must be a normalized eBay search like "2018 Panini Prizm Luka Doncic #280 Silver".
- Grade as a RANGE. A phone photo cannot distinguish PSA 9 from 10 — be honest about the spread.
- Authenticity red_flags are warning signs (print dot pattern, era-inconsistent fonts/logos,
  gloss, miscut suggesting a reprint sheet), NOT a certification.
- If photo_ok is false, set identity/condition/authenticity to null.

PSA grading scale for reference:
{scale}"""

def parse_vision_json(raw: str) -> VisionResult:
    cleaned = _FENCE_RE.sub("", raw.strip())
    try:
        return VisionResult.model_validate(json.loads(cleaned))
    except (json.JSONDecodeError, ValidationError) as e:
        raise VisionParseError(f"Model returned unparseable analysis: {type(e).__name__}") from e
```

Create empty `server/app/vision/__init__.py`.

**Step 4: Run — verify PASS. Step 5: Commit**

```bash
git add server/app/vision server/tests/test_vision_prompt.py && git commit -m "feat(server): vision prompt and strict JSON parsing"
```

---

### Task 10: Vision provider clients (BYO-AI)

Raw httpx calls to Anthropic and OpenAI (no SDKs — fewer deps for an OSS project, and `MockTransport` testing is uniform). The user's key is passed per-call and never stored.

**Files:**
- Create: `server/app/vision/providers.py`
- Test: `server/tests/test_vision_providers.py`

**Step 1: Write the failing tests**

```python
import httpx
import pytest
from app.vision.providers import analyze_card, ProviderAuthError

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
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`server/app/vision/providers.py`:

```python
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

async def _call_anthropic(http, front, front_type, back, api_key, model) -> str:
    content = [{"type": "image",
                "source": {"type": "base64", "media_type": front_type, "data": _b64(front)}}]
    if back:
        content.append({"type": "image",
                        "source": {"type": "base64", "media_type": back[1], "data": _b64(back[0])}})
    content.append({"type": "text", "text": build_prompt()})
    resp = await http.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        json={"model": model, "max_tokens": 2048,
              "messages": [{"role": "user", "content": content}]},
    )
    _raise_for_provider_status(resp)
    return "".join(b.get("text", "") for b in resp.json()["content"] if b.get("type") == "text")

async def _call_openai(http, front, front_type, back, api_key, model) -> str:
    content = [{"type": "image_url",
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
```

**Step 4: Run — verify PASS. Step 5: Commit**

```bash
git add server/app/vision/providers.py server/tests/test_vision_providers.py && git commit -m "feat(server): BYO-AI vision providers (anthropic, openai)"
```

---

### Task 11: `POST /api/scan` orchestration

Ties the pipeline together with partial-results error handling. Tests monkeypatch the stage functions — no network.

**Files:**
- Modify: `server/app/main.py`
- Create: `server/app/scan.py`
- Test: `server/tests/test_scan_endpoint.py`

**Step 1: Write the failing tests**

```python
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import scan as scan_module
from app.schemas import (VisionResult, Identity, Condition, Authenticity, CompListing)
from app.vision.providers import ProviderAuthError

GOOD_VISION = VisionResult(
    photo_ok=True,
    identity=Identity(player="Luka Doncic", year="2018", set_name="Panini Prizm",
                      card_number="280", search_string="2018 Panini Prizm Luka Doncic #280",
                      confidence=0.92),
    condition=Condition(observations=[], grade_low=6, grade_high=8),
    authenticity=Authenticity(red_flags=[], risk="low"),
)
LISTINGS = [CompListing(title=f"Luka raw {i}", price=50.0 + i, graded=False) for i in range(4)]

def post_scan(client, **form):
    return client.post("/api/scan",
        files={"front": ("card.jpg", io.BytesIO(b"fake"), "image/jpeg")},
        data=form,
        headers={"X-AI-Provider": "anthropic", "X-AI-Key": "k"})

@pytest.fixture
def client():
    return TestClient(app)

def test_full_scan_happy_path(client, monkeypatch):
    async def fake_vision(*a, **k): return GOOD_VISION
    async def fake_search(q): return LISTINGS
    monkeypatch.setattr(scan_module, "run_vision", fake_vision)
    monkeypatch.setattr(scan_module, "search_comps", fake_search)
    resp = post_scan(client, asking_price="30")
    assert resp.status_code == 200
    body = resp.json()
    assert body["vision"]["identity"]["player"] == "Luka Doncic"
    assert body["comps"]["raw_count"] == 4
    assert body["verdict"]["verdict"] == "undervalued"

def test_bad_photo_short_circuits(client, monkeypatch):
    async def fake_vision(*a, **k):
        return VisionResult(photo_ok=False, photo_issue="too much glare")
    monkeypatch.setattr(scan_module, "run_vision", fake_vision)
    body = post_scan(client).json()
    assert body["vision"]["photo_ok"] is False
    assert body["comps"] is None and body["verdict"] is None

def test_ebay_failure_returns_partial(client, monkeypatch):
    async def fake_vision(*a, **k): return GOOD_VISION
    async def broken_search(q): raise RuntimeError("ebay down")
    monkeypatch.setattr(scan_module, "run_vision", fake_vision)
    monkeypatch.setattr(scan_module, "search_comps", broken_search)
    body = post_scan(client, asking_price="30").json()
    assert body["vision"]["identity"] is not None
    assert body["comps"] is None and body["comps_error"]
    assert body["verdict"] is None

def test_invalid_ai_key_is_401(client, monkeypatch):
    async def fake_vision(*a, **k): raise ProviderAuthError("bad key")
    monkeypatch.setattr(scan_module, "run_vision", fake_vision)
    assert post_scan(client).status_code == 401

def test_missing_headers_is_422(client):
    resp = client.post("/api/scan",
        files={"front": ("card.jpg", io.BytesIO(b"fake"), "image/jpeg")})
    assert resp.status_code == 422
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`server/app/scan.py`:

```python
from typing import Optional
from app.comps import summarize
from app.config import get_settings
from app.ebay import EbayClient
from app.schemas import CompListing, ScanResponse, VisionResult
from app.verdict import decide
from app.vision.providers import analyze_card

_ebay_client: Optional[EbayClient] = None

async def run_vision(front: bytes, front_type: str, back, provider: str,
                     api_key: str, model: str) -> VisionResult:
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

async def perform_scan(front: bytes, front_type: str, back, provider: str,
                       api_key: str, model: str,
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
```

Add to `server/app/main.py`:

```python
from typing import Annotated, Optional
from fastapi import File, Form, Header, HTTPException, UploadFile
from app import scan as scan_module
from app.config import get_settings
from app.schemas import ScanResponse
from app.vision.prompt import VisionParseError
from app.vision.providers import ProviderAuthError, ProviderRateLimited

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
    model = x_ai_model or (settings.anthropic_default_model if x_ai_provider == "anthropic"
                           else settings.openai_default_model)
    front_bytes = await front.read()
    back_tuple = None
    if back is not None:
        back_tuple = (await back.read(), back.content_type or "image/jpeg")
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
```

**Step 4: Run — verify PASS (full suite). Step 5: Commit**

```bash
git add server/app && git add server/tests/test_scan_endpoint.py && git commit -m "feat(server): scan endpoint with partial-results orchestration"
```

---

### Task 12: Web scaffold (Vite + React + TS + vitest)

**Files:**
- Create: `web/` via scaffolder, then `web/vitest.config.ts`

**Step 1: Scaffold**

```bash
cd <repo-root>
npm create vite@latest web -- --template react-ts
cd web && npm install
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

**Step 2: Configure vitest**

`web/vitest.config.ts`:

```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: { environment: 'jsdom', globals: true },
})
```

Add to `web/package.json` scripts: `"test": "vitest run"`.
Delete boilerplate: `web/src/App.css` contents, `web/src/assets/react.svg` usage — leave `App.tsx` returning `<h1>Card Scanner</h1>` for now.

**Step 3: Verify**

Run: `npm run build && npm test` — expected: build succeeds; vitest reports "no test files found" exit 0 (pass `--passWithNoTests` in the script).

**Step 4: Commit**

```bash
git add web && git commit -m "feat(web): Vite React TS scaffold with vitest"
```

---

### Task 13: Types + localStorage helpers

**Files:**
- Create: `web/src/types.ts`, `web/src/storage.ts`
- Test: `web/src/storage.test.ts`

**Step 1: Create `web/src/types.ts`** — mirror `server/app/schemas.py` field-for-field (snake_case, matching the JSON): `Identity`, `AreaObservation`, `Condition`, `Authenticity`, `VisionResult`, `CompsSummary`, `Verdict`, `ScanResponse`, plus:

```ts
export type Provider = 'anthropic' | 'openai'
export interface AiSettings { provider: Provider; apiKey: string; model?: string }
export interface HistoryEntry { at: string; response: ScanResponse; askingPrice?: number }
```

**Step 2: Write the failing tests**

`web/src/storage.test.ts`:

```ts
import { beforeEach, expect, test } from 'vitest'
import { loadSettings, saveSettings, loadHistory, pushHistory, HISTORY_LIMIT } from './storage'

beforeEach(() => localStorage.clear())

test('settings round-trip', () => {
  expect(loadSettings()).toBeNull()
  saveSettings({ provider: 'anthropic', apiKey: 'sk-x' })
  expect(loadSettings()?.apiKey).toBe('sk-x')
})

test('history caps at limit, newest first', () => {
  for (let i = 0; i < HISTORY_LIMIT + 5; i++) {
    pushHistory({ at: `t${i}`, response: { vision: { photo_ok: false } } as never })
  }
  const h = loadHistory()
  expect(h.length).toBe(HISTORY_LIMIT)
  expect(h[0].at).toBe(`t${HISTORY_LIMIT + 4}`)
})

test('corrupt storage returns empty, not crash', () => {
  localStorage.setItem('cardscanner.history', '{not json')
  expect(loadHistory()).toEqual([])
})
```

**Step 3: Run — verify FAIL. Step 4: Implement**

`web/src/storage.ts`:

```ts
import type { AiSettings, HistoryEntry } from './types'

const SETTINGS_KEY = 'cardscanner.settings'
const HISTORY_KEY = 'cardscanner.history'
export const HISTORY_LIMIT = 50

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

export const loadSettings = () => read<AiSettings>(SETTINGS_KEY)
export const saveSettings = (s: AiSettings) => localStorage.setItem(SETTINGS_KEY, JSON.stringify(s))
export const loadHistory = () => read<HistoryEntry[]>(HISTORY_KEY) ?? []
export function pushHistory(entry: HistoryEntry) {
  const next = [entry, ...loadHistory()].slice(0, HISTORY_LIMIT)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next))
}
```

**Step 5: Run — verify PASS, commit**

```bash
git add web/src/types.ts web/src/storage.ts web/src/storage.test.ts && git commit -m "feat(web): types and localStorage helpers"
```

---

### Task 14: API client

**Files:**
- Create: `web/src/api.ts`
- Test: `web/src/api.test.ts`

**Step 1: Write the failing tests**

```ts
import { afterEach, expect, test, vi } from 'vitest'
import { scanCard, ApiError } from './api'

const settings = { provider: 'anthropic' as const, apiKey: 'sk-x' }
const file = new File(['x'], 'card.jpg', { type: 'image/jpeg' })

afterEach(() => vi.restoreAllMocks())

test('posts multipart with AI headers', async () => {
  const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ vision: { photo_ok: false } }), { status: 200 }))
  await scanCard(file, null, 30, settings)
  const [url, init] = mock.mock.calls[0]
  expect(String(url)).toContain('/api/scan')
  expect((init!.headers as Record<string, string>)['X-AI-Key']).toBe('sk-x')
  expect(init!.body).toBeInstanceOf(FormData)
})

test('maps 401 to a settings hint', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ detail: 'Your AI provider rejected the API key. Check it in Settings.' }),
      { status: 401 }))
  await expect(scanCard(file, null, null, settings)).rejects.toThrow(/Settings/)
})

test('network failure gives readable error', async () => {
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('fetch failed'))
  await expect(scanCard(file, null, null, settings)).rejects.toThrow(ApiError)
})
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`web/src/api.ts`:

```ts
import type { AiSettings, ScanResponse } from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {}

export async function scanCard(front: File, back: File | null,
                               askingPrice: number | null,
                               settings: AiSettings): Promise<ScanResponse> {
  const form = new FormData()
  form.append('front', front)
  if (back) form.append('back', back)
  if (askingPrice != null) form.append('asking_price', String(askingPrice))

  const headers: Record<string, string> = {
    'X-AI-Provider': settings.provider,
    'X-AI-Key': settings.apiKey,
  }
  if (settings.model) headers['X-AI-Model'] = settings.model

  let resp: Response
  try {
    resp = await fetch(`${API_BASE}/api/scan`, { method: 'POST', body: form, headers })
  } catch {
    throw new ApiError('Could not reach the scan server. Check your connection.')
  }
  if (!resp.ok) {
    const detail = await resp.json().then(b => b.detail).catch(() => null)
    throw new ApiError(detail ?? `Scan failed (${resp.status}). Try again.`)
  }
  return resp.json()
}
```

**Step 4: Run — verify PASS. Step 5: Commit**

```bash
git add web/src/api.ts web/src/api.test.ts && git commit -m "feat(web): scan API client"
```

---

### Task 15: App shell + Settings screen

Simple state-based views — no router (YAGNI): `'scan' | 'results' | 'settings' | 'history'`.

**Files:**
- Modify: `web/src/App.tsx`
- Create: `web/src/screens/SettingsScreen.tsx`
- Test: `web/src/screens/SettingsScreen.test.tsx`

**Step 1: Write the failing test**

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { beforeEach, expect, test } from 'vitest'
import SettingsScreen from './SettingsScreen'
import { loadSettings } from '../storage'

beforeEach(() => localStorage.clear())

test('saves provider and key', () => {
  render(<SettingsScreen onDone={() => {}} />)
  fireEvent.change(screen.getByLabelText(/provider/i), { target: { value: 'openai' } })
  fireEvent.change(screen.getByLabelText(/api key/i), { target: { value: 'sk-test' } })
  fireEvent.click(screen.getByRole('button', { name: /save/i }))
  expect(loadSettings()).toMatchObject({ provider: 'openai', apiKey: 'sk-test' })
})
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`web/src/screens/SettingsScreen.tsx`:

```tsx
import { useState } from 'react'
import { loadSettings, saveSettings } from '../storage'
import type { Provider } from '../types'

export default function SettingsScreen({ onDone }: { onDone: () => void }) {
  const existing = loadSettings()
  const [provider, setProvider] = useState<Provider>(existing?.provider ?? 'anthropic')
  const [apiKey, setApiKey] = useState(existing?.apiKey ?? '')

  return (
    <div className="screen">
      <h2>Bring your own AI</h2>
      <p>Scans run on your own AI account. Your key is stored only on this device
         and sent only to your chosen provider.</p>
      <label>
        Provider
        <select value={provider} onChange={e => setProvider(e.target.value as Provider)}>
          <option value="anthropic">Anthropic (Claude)</option>
          <option value="openai">OpenAI</option>
        </select>
      </label>
      <label>
        API key
        <input type="password" value={apiKey} placeholder="sk-..."
               onChange={e => setApiKey(e.target.value)} />
      </label>
      <button disabled={!apiKey} onClick={() => { saveSettings({ provider, apiKey }); onDone() }}>
        Save
      </button>
    </div>
  )
}
```

`web/src/App.tsx` — view switcher: if no settings saved, force `settings` view; header with app title, History and Settings buttons; renders the active screen (Scan/Results/History screens arrive in Tasks 16–17; stub them as `<p>coming soon</p>` placeholders so the app compiles).

**Step 4: Run — verify PASS (`npm test`), and `npm run build` succeeds. Step 5: Commit**

```bash
git add web/src && git commit -m "feat(web): app shell and BYO-AI settings screen"
```

---

### Task 16: Scan screen (camera capture + asking price)

**Files:**
- Create: `web/src/screens/ScanScreen.tsx`
- Modify: `web/src/App.tsx` (replace stub)

**Step 1: Implement** (presentational; camera inputs are hard to unit test meaningfully — the field test covers this)

```tsx
import { useState } from 'react'

interface Props { onSubmit: (front: File, back: File | null, askingPrice: number | null) => void
                  busy: boolean }

export default function ScanScreen({ onSubmit, busy }: Props) {
  const [front, setFront] = useState<File | null>(null)
  const [back, setBack] = useState<File | null>(null)
  const [ask, setAsk] = useState('')

  return (
    <div className="screen">
      <label className="capture">
        {front ? <img src={URL.createObjectURL(front)} alt="card front" /> : 'Tap to photograph card front'}
        <input type="file" accept="image/*" capture="environment" hidden
               onChange={e => setFront(e.target.files?.[0] ?? null)} />
      </label>
      <label className="capture small">
        {back ? <img src={URL.createObjectURL(back)} alt="card back" /> : '+ back (optional)'}
        <input type="file" accept="image/*" capture="environment" hidden
               onChange={e => setBack(e.target.files?.[0] ?? null)} />
      </label>
      <label>
        Asking price (optional)
        <input type="number" inputMode="decimal" placeholder="$" value={ask}
               onChange={e => setAsk(e.target.value)} />
      </label>
      <button disabled={!front || busy}
              onClick={() => onSubmit(front!, back, ask ? Number(ask) : null)}>
        {busy ? 'Scanning…' : 'Scan card'}
      </button>
    </div>
  )
}
```

Wire into `App.tsx`: on submit call `scanCard(...)` with saved settings, `pushHistory` on success, switch to `results` view; on error show the message inline (keep it on the scan screen). Track `busy` during the call.

**Step 2: Verify** — `npm run build && npm test` pass.

**Step 3: Commit**

```bash
git add web/src && git commit -m "feat(web): camera capture scan screen"
```

---

### Task 17: Results screen + history

**Files:**
- Create: `web/src/screens/ResultsScreen.tsx`, `web/src/screens/HistoryScreen.tsx`
- Test: `web/src/screens/ResultsScreen.test.tsx`
- Modify: `web/src/App.tsx` (replace stubs)

**Step 1: Write the failing tests**

```tsx
import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import ResultsScreen from './ResultsScreen'
import type { ScanResponse } from '../types'

const base: ScanResponse = {
  vision: {
    photo_ok: true, photo_issue: null,
    identity: { player: 'Luka Doncic', year: '2018', set_name: 'Panini Prizm',
                card_number: '280', variant: null,
                search_string: '2018 Panini Prizm Luka Doncic #280', confidence: 0.92 },
    condition: { observations: [], grade_low: 6, grade_high: 8 },
    authenticity: { red_flags: [], risk: 'low' }, ai_value_note: null,
  },
  comps: { source: 'active_listings', raw_count: 4, raw_low: 60, raw_median: 90,
           graded_count: 0, graded_low: null, graded_median: null },
  comps_error: null,
  verdict: { value_low: 60, value_high: 90, verdict: 'undervalued', reasoning: 'Cheap!' },
}

test('shows identity, grade range, and verdict', () => {
  render(<ResultsScreen result={base} onRescan={() => {}} />)
  expect(screen.getByText(/Luka Doncic/)).toBeTruthy()
  expect(screen.getByText(/PSA 6–8/)).toBeTruthy()
  expect(screen.getByText(/undervalued/i)).toBeTruthy()
})

test('bad photo shows retake prompt', () => {
  const r: ScanResponse = { vision: { photo_ok: false, photo_issue: 'too much glare',
    identity: null, condition: null, authenticity: null, ai_value_note: null },
    comps: null, comps_error: null, verdict: null }
  render(<ResultsScreen result={r} onRescan={() => {}} />)
  expect(screen.getByText(/glare/)).toBeTruthy()
  expect(screen.getByRole('button', { name: /retake/i })).toBeTruthy()
})

test('comps failure still shows grade with value unavailable', () => {
  const r = { ...base, comps: null, verdict: null, comps_error: 'eBay down' }
  render(<ResultsScreen result={r} onRescan={() => {}} />)
  expect(screen.getByText(/PSA 6–8/)).toBeTruthy()
  expect(screen.getByText(/value unavailable/i)).toBeTruthy()
})

test('authenticity red flags surface prominently', () => {
  const r = structuredClone(base)
  r.vision.authenticity = { red_flags: ['print pattern looks off'], risk: 'high' }
  render(<ResultsScreen result={r} onRescan={() => {}} />)
  expect(screen.getByText(/print pattern looks off/)).toBeTruthy()
})
```

**Step 2: Run — verify FAIL. Step 3: Implement**

`ResultsScreen.tsx` renders, top to bottom: retake prompt (if `!photo_ok`, with `photo_issue` and a Retake button calling `onRescan`); identity block (player, year/set/number, low-confidence warning under 0.5); authenticity banner (risk color: low=green, caution=amber, high=red; list red flags); grade range as `PSA {grade_low}–{grade_high}` with the observation list; value block — verdict badge + reasoning when present, "Market value unavailable" + `comps_error` (and `ai_value_note` fallback labeled "AI rough estimate — low confidence") otherwise; "which data source" caption from `comps.source`. `HistoryScreen.tsx` lists `loadHistory()` entries (player, date, verdict badge), tapping one shows it in ResultsScreen.

**Step 4: Run — verify PASS. Step 5: Commit**

```bash
git add web/src && git commit -m "feat(web): results and history screens"
```

---

### Task 18: PWA manifest + mobile styles

**Files:**
- Modify: `web/index.html`, `web/src/index.css`
- Create: `web/public/manifest.webmanifest`, `web/public/icon.svg`

**Step 1: Manifest** — name "Card Scanner", `display: standalone`, theme color, SVG icon (a simple card outline is fine). Link it plus `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">` and `<meta name="theme-color">` in `index.html`.

**Step 2: Styles** — `index.css`: mobile-first single column, max-width 480px centered; large tap targets (min 44px); `.capture` as a large dashed-border card-aspect-ratio (2.5/3.5) drop zone; verdict badge colors (undervalued=green, fair=neutral, overpriced=red, others=gray). Keep it clean and minimal — no CSS framework.

**Step 3: Verify** — `npm run build`; open dev server on a phone (`npm run dev -- --host`) and confirm the camera opens from the capture input.

**Step 4: Commit**

```bash
git add web && git commit -m "feat(web): PWA manifest and mobile-first styles"
```

---

### Task 19: Golden-set fixtures + integration test

**Files:**
- Create: `server/tests/fixtures/` (recorded JSON), `server/tests/test_integration.py`

**Step 1:** Save two recorded provider responses as fixtures: `vision_luka_good.json` (the full VisionResult JSON from Task 9's test) and `ebay_luka_search.json` (Browse API shape from Task 8's test, ~10 items mixing raw/PSA titles).

**Step 2: Write the integration test** — wire `/api/scan` end-to-end using `httpx.MockTransport`s fed by the fixture files (monkeypatch `scan_module._ebay_client` with a fixture-backed `EbayClient`, and patch `app.vision.providers.analyze_card`'s transport via a wrapper). Assert: 200, identity correct, comps buckets correct, verdict matches hand-computed expectation. Also add `test_verdict_golden`: for 3 hand-built (comps, condition, ask) triples, assert exact verdict labels — these pin the thresholds against accidental change.

**Step 3: Run — full suite passes: `pytest -v` (expect ~25 tests). Step 4: Commit**

```bash
git add server/tests && git commit -m "test(server): golden fixtures and end-to-end scan integration test"
```

---

### Task 20: Open-source packaging — README, DEPLOY, Makefile, CI

**Files:**
- Create: `Makefile`, `DEPLOY.md`, `.github/workflows/ci.yml`
- Modify: `README.md` (full rewrite)

**Step 1: Makefile** (repo root):

```makefile
.PHONY: dev server web test
server:
	cd server && .venv/bin/uvicorn app.main:app --reload --port 8000
web:
	cd web && npm run dev
dev:
	$(MAKE) -j2 server web
test:
	cd server && .venv/bin/pytest -q
	cd web && npm test
```

**Step 2: CI** — `.github/workflows/ci.yml`: two jobs on push/PR — `server` (setup-python 3.12, `pip install -e "server[dev]"` … `pytest`) and `web` (setup-node 22, `npm ci`, `npm test`, `npm run build`). No secrets needed — that's the point of the mocked tests.

**Step 3: README rewrite** — product-first: what it does (photo → identity, grade range, authenticity flags, eBay-priced verdict), a Quick Start (clone → `python -m venv` + pip install → `npm install` → copy `.env.example` → `make dev`), BYO-AI explanation (your key, your device, your provider), eBay setup (free dev account, which two env vars, app works without them minus pricing), honest-limitations section (grade is a range from a phone photo, not a certification; authenticity flags are warnings; v1 prices from active listings, sold-price upgrade pending eBay approval), architecture sketch, license badge. Link `docs/plans/` for design history.

**Step 4: DEPLOY.md** — Fly.io/Railway walkthrough: deploy `server/` (uvicorn, port 8000, set two eBay env vars), build `web/` with `VITE_API_URL` pointing at the server, serve `web/dist` on any static host (or mount into FastAPI with `StaticFiles` — document the one-service option).

**Step 5: Verify & commit**

Run `make test` — everything green.

```bash
git add Makefile DEPLOY.md .github README.md && git commit -m "docs: open-source packaging — README, deploy guide, CI"
```

---

## Definition of done (v1)

- [ ] `make test` green (server + web), CI green on GitHub
- [ ] Phone test: camera capture → results screen renders all four blocks
- [ ] Degraded paths verified by hand: bad key (401 message), no eBay creds (partial result), blurry photo (retake prompt)
- [ ] Card-show field test: 20 scans — count correct identities, trusted verdicts (acceptance gate from the design doc)
