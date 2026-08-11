# Card Scanner

[![CI](https://img.shields.io/badge/CI-GitHub_Actions-blue)](.github/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Point your phone at a sports card and get an answer: what it is, what shape it's in, and whether the price is right.

- **Identity** — player, year, set, card number, parallel/variation.
- **Grade range** — a realistic condition estimate (e.g. "PSA 6–8") from your photo.
- **Authenticity red flags** — warning signs like print pattern anomalies or trimmed edges.
- **Verdict** — priced against live eBay comps: **undervalued**, **fair**, or **overpriced**.

## How it works

```
┌────────────┐    ┌──────────────────┐    ┌───────────────┐    ┌─────────────┐
│ Card photo │ ─▶ │ BYO-AI vision    │ ─▶ │ eBay comps    │ ─▶ │   Verdict   │
│ (phone cam)│    │ (your API key)   │    │ (live search) │    │ under/fair/ │
└────────────┘    │ identity + grade │    │ price stats   │    │ overpriced  │
                  └──────────────────┘    └───────────────┘    └─────────────┘
```

1. You snap the card (front, optionally back) in the web app.
2. The stateless API server forwards the photo to **your** AI provider for identification, grading, and authenticity checks.
3. The server searches eBay for comparable listings and computes price statistics.
4. You get a verdict comparing the listing price you entered against the comps.

## Bring your own AI key

There is no shared backend account and no markup. You paste your own API key in the app's settings:

- Your key is stored **only in your browser** (localStorage) and sent **only to your provider** (relayed per-request by the stateless server, never logged or stored).
- Supported providers: **Anthropic** and **OpenAI**.
- Per-scan cost is billed to you by your provider — typically a few cents per scan.

## Quick start

```bash
git clone https://github.com/YOUR_USER/SportsCardGrader.git
cd SportsCardGrader
make setup                # python venv + server deps, npm install for web
cp .env.example .env      # optional — eBay credentials (see below)
make dev                  # API on :8000, web app on :5173
```

Open http://localhost:5173. The Vite dev server proxies `/api` to `http://localhost:8000` (configured in `web/vite.config.ts`), so no `VITE_API_URL` is needed in development. For production builds, set `VITE_API_URL` to your server's URL (see [DEPLOY.md](DEPLOY.md)).

The API server reads its config from environment variables; `make server` sources the repo-root `.env` automatically before starting uvicorn, so keep your `.env` at the repo root.

Requirements: Python 3.12+, Node 22+.

### eBay setup (optional)

Create a free account at [developer.ebay.com](https://developer.ebay.com), create an app, and put its keys in `.env`:

```
EBAY_CLIENT_ID=your-client-id
EBAY_CLIENT_SECRET=your-client-secret
```

Without them the app still works — scans just won't include market prices or a value verdict.

## Honest limitations

- **The grade is a range, not a certification.** It's an estimate from a phone photo. Surface flaws, print lines, and edge wear that graders catch under magnification may be invisible in your shot.
- **Authenticity flags are warning signs only** — they are not proof either way. High-value cards deserve professional authentication.
- **v1 prices come from active eBay listings** — asking prices, not sold prices. Asks skew high. (Sold-data API access is pending.)
- **The verdict needs 3+ comparable raw listings**; with fewer, it honestly says "not enough data" instead of guessing.

## Architecture

- **`server/`** — FastAPI, fully stateless. BYO-AI passthrough (your key travels request → provider and is never persisted), eBay Browse API client, verdict logic. No database.
- **`web/`** — Vite + React PWA. Camera capture, results, scan history. All state (settings, history) lives in localStorage — nothing leaves your device except the scan request itself.

Design history and decisions: [`docs/plans/`](docs/plans/).

## Testing

```bash
make test
```

Server tests use mocked AI and eBay responses — no credentials or network needed, so CI is green for every contributor out of the box.

## Contributing

Contributions welcome — open an issue or PR. Please keep `make test` green.

## License

[MIT](LICENSE)
