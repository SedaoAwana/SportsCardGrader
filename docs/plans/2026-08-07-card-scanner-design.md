# Card Scanner — Design

**Date:** 2026-08-07
**Status:** Approved (brainstorming session with Calvin)

## Vision

A mobile-first, open-source web app for casual collectors and flippers: point
your phone at a sports card and get, in one scan —

1. **Identity** — what card this is
2. **Grade estimate** — rough condition as a grade *range*
3. **Authenticity red flags** — counterfeit/reprint warning signs
4. **Value & verdict** — what it sells for, and whether the asking price in
   front of you is **undervalued / fair / overpriced**

A marketplace deal-discovery feed ("browse mispriced listings") is the v2
vision; v1 proves the valuation engine inside the scan flow first.

## Key decisions

| Decision | Choice | Why |
|---|---|---|
| Target user | Casual collectors/flippers at shows, garage sales, pack rips | Fast "point and know" beats deep analytics |
| Undervalued feature | Verdict inside the scan flow (v1); marketplace feed later (v2) | Phased; scan flow proves the valuation engine |
| Platform | Mobile-first PWA now, native later | Shareable link, no app store, one codebase |
| AI | **BYO-AI**: users bring their own OpenAI/Anthropic API key | Zero bundled inference cost; essential for open source |
| Price data | eBay APIs (deployer's own free dev credentials) | Ground truth for real prices |
| v1 success | A shareable link that Calvin + collector friends trust at a real card show | No accounts, no scan history server-side |
| Licensing | Open source, MIT | Anyone can clone and launch their own instance |

## Why a rebuild (not incremental)

Code review of the prior codebase (2026-08-06) found the OpenCV grading
pipeline measured the wrong things entirely — e.g. "centering" measured the
card's position in the photo frame, not the image within the card borders;
"corner sharpness" was the mean Sobel gradient of the whole image. The API
server simulated async job progress while running synchronously. The output
looked authoritative (real PSA descriptions) but was noise — worse than no
grader for a tool advising purchases. Salvaged: the PSA grade-scale reference
data, the atomic-design frontend concept, and the repo itself.

## Architecture

```
SportsCardGrader/
├── web/        Vite + React + TypeScript PWA (mobile-first)
├── server/     FastAPI backend — thin, stateless orchestrator
└── docs/plans/ design + implementation docs
```

### web/ (PWA)

- Opens straight to camera capture (`<input capture>`); front photo required,
  back optional; user can type the asking price they see at the table.
- Installable PWA; scan history in `localStorage` (no accounts).
- Settings screen: paste AI provider API key (OpenAI or Anthropic). Key lives
  only in `localStorage`, sent per-request in a header. Designed so provider
  OAuth can slot in later if providers ship API-granting sign-in.

### server/ (FastAPI)

- Stateless, no DB, no queue. `POST /scan` takes image(s) + optional asking
  price + user's AI key in a header; returns one JSON result synchronously.
- Passes the AI key through to the provider; never logs or persists it.
- eBay credentials are the **deployer's own** (env vars).
- Deploys as one small service (Fly.io/Railway class).

## Scan pipeline

### Stage 1 — Vision analysis (user's AI provider)

Structured-output prompt returns one JSON object:

- **Identity:** player, year, set, card number, parallel/variant, normalized
  search string (e.g. `2018 Panini Prizm Luka Doncic #280 Silver`), plus a
  confidence score. Low identity confidence is surfaced, never hidden —
  everything downstream depends on it.
- **Condition:** per-area observations (corners, edges, surface, centering)
  with severity notes, rolled into an estimated grade **range** (e.g.
  "PSA 6–8"). Never a fake-precise single number: phone photos cannot
  distinguish a 9 from a 10, and the product says so.
- **Authenticity:** red-flag list (print dot pattern, era-inconsistent
  font/logo, gloss, miscut suggesting reprint sheet) with risk level
  `low / caution / high`. Framed as warning signs, explicitly **not** a
  certification.
- **Photo quality:** if too blurry/glared to judge, the model says so and the
  app prompts a retake instead of emitting garbage.

The PSA grade-scale reference data (labels, descriptions, centering
tolerances) carried over from the old repo grounds the prompt and the UI copy.

### Stage 2 — Market comps (eBay, server credentials)

- Query eBay with the identity search string; split raw vs. graded buckets.
- True sold-price data (Marketplace Insights API) requires eBay approval —
  application to be filed. Until granted, v1 uses **active-listing lowest
  asks**, a defensible baseline for the card-show question ("table wants $30,
  listed from $80 online"). Responses label which data source was used.

### Stage 3 — Verdict (pure functions, server)

- Grade range × comps distribution → value range.
- Compared against typed asking price → **undervalued / fair / overpriced**,
  with reasoning shown ("raw copies list $60–90; even the low end of its
  condition range beats the $30 ask").
- Low identity confidence or thin comps → verdict downgrades to "not enough
  data" rather than guessing.

## Error handling

Every degraded path returns **partial results** — a scan never all-or-nothing
fails because one stage hiccuped.

- Invalid/expired AI key → clear prompt to the settings screen.
- Provider rate limit → retry once, then human-readable message.
- No comps found → AI's rough value estimate, clearly labeled low-confidence.
- eBay API down → identity/grade/authenticity still returned; value marked
  unavailable.

## Testing

- **Golden set:** real card photos (Calvin's collection + `sample_images/`)
  with known identities as fixtures.
- **Verdict engine:** pytest unit tests — it is pure math, test it hard.
- **Integration:** recorded provider/eBay responses so CI needs no live keys.
- **Acceptance:** card-show field checklist — 20 scans; count correct
  identities and verdicts you'd actually trust.

## Open source & self-hosting

- MIT license.
- All deployer credentials via env vars; nothing secret in the repo.
- One-command local run (`docker compose up` or `make dev`); short DEPLOY.md
  for Fly.io/Railway — clone → add env vars → deploy.
- README rewritten around the product with an architecture sketch so
  contributors orient in five minutes.

## Out of scope for v1 (v2 candidates)

- Marketplace deal-discovery feed (listing ingestion, background jobs)
- Accounts, server-side scan history
- Native mobile app
- Provider OAuth sign-in
- Sold-price data via Marketplace Insights (pending eBay approval)
