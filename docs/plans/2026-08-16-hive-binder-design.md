# Hive-Backed Storage for SportsCardGrader ("The Binder")

## Context

SportsCardGrader (`/Users/sedao/SportsCardGrader` — FastAPI server + Vite/React 19 PWA) is deliberately stateless: scan history lives in browser localStorage (`web/src/storage.ts`, 50-entry cap, no images), and nothing persists server-side. Calvin wants durable storage for cards, images, card metadata, and eBay sales/comps data **without running a conventional database**.

Decided architecture (confirmed with Calvin):
- **Client-side staging**: scans + comps data accumulate locally until a payload is ready. Upgrade localStorage → IndexedDB so image blobs fit.
- **Hive community as the database**: ready payloads are published as posts to Hive community **`hive-192941`** ("The Binder", verified on-chain, created 2026-08-16, admin @meno; visible on snapie.io / peakd.com). The community feed is read back via Hivemind bridge API — no DB.
- **Central app account** signs everything: the FastAPI server holds one Hive account's posting key (env var) and publishes on users' behalf; users don't need Hive accounts. Attribution via anonymous client UUID in `json_metadata`.
- **Images** → images.hive.blog (free permanent CDN, signed with the app posting key; fallback images.3speak.tv).

## Key design decisions

| Decision | Choice |
|---|---|
| Post shape | Every card = root post in hive-192941 (browsable on Snapie/PeakD). Escape hatch if volume > ~200/day: cards as comments under daily anchor posts (documented, not built). |
| Python Hive lib | **lighthive** for signing/broadcast (small, maintained, pure Python; beem is stale); raw async httpx JSON-RPC with node failover for reads. Broadcasts run in `asyncio.to_thread`. |
| Rewards | Decline payout (`comment_options` `max_accepted_payout: '0.000 HBD'` in same tx) — avoids reward-farming optics on auto-posted content. |
| Duplicate safety | Deterministic permlink `card-{player-slug≤32}-{year}-{sha256(record_id)[:8]}` + existence check before broadcast + **never blind-retry a broadcast** (on error: wait ~9s, check chain, only then re-attempt with backoff). |
| Publish queue | File-backed (one JSON per job in `server/data/publish_queue/`, atomic tmp+rename). Single-process worker — fine since the chain caps us at 1 root post/5 min anyway. |
| Updates (comps refresh) | Re-broadcast same author/permlink = edit; goes through the same queue (15s spacing; edits don't hit the 5-min root-post cooldown). |
| Client store | IndexedDB via `idb` package; settings stay in localStorage; `fake-indexeddb` for tests. |

## Data model

Canonical card record embedded in the post's `json_metadata.card` (pydantic in new `server/app/hive/record.py`, mirrored in `web/src/binderTypes.ts` — same convention as existing `schemas.py`/`types.ts` pairing). Reuses existing `Identity`, `Condition`, `Slab`, `Authenticity`, `Verdict`, `CompsSummary`, `CompListing` schemas verbatim:

```json
{
  "app": "cardscanner/1.0", "format": "markdown",
  "tags": ["hive-192941", "sportscards", "cardscanner", "sc-luka-doncic", "sc-2018", "sc-prizm"],
  "image": ["https://images.hive.blog/DQm.../front.jpg"],
  "card": {
    "v": 1, "kind": "card", "record_id": "<client uuid4 — idempotency key>",
    "identity": {}, "condition": {}, "slab": {}, "authenticity": {}, "verdict": {},
    "comps": {"summary": {}, "top_sales": ["<capped at 10>"], "as_of": "ISO"},
    "images": {"front": "url", "back": "url|null"},
    "asking_price": null,
    "attribution": {"client_id": "<anon uuid>", "display_name": null},
    "scanned_at": "ISO"
  }
}
```

- First tag MUST be `hive-192941` (community assignment). Derived tags `sc-<player>`, `sc-<year>`, `sc-<set>` (lowercase slugs, ≤8 tags) enable per-player tag queries; the community feed is the primary index.
- Post body = human-readable markdown (image, stats table, comps summary line) so The Binder is browsable on Hive frontends.
- Size guard: serialized json_metadata < 8 KB (unit-tested); tx limit is 64 KB.

## Server changes

New package `server/app/hive/`:
1. **`client.py`** — `HiveClient`: async JSON-RPC over httpx with node failover (api.hive.blog, api.deathwing.me, api.openhive.network, anyx.io, …), `get_post`, `get_ranked_posts`, `get_rc_percent` (rc_api), `broadcast_card_post` ([comment, comment_options] ops via lighthive in a thread; `HIVE_DRY_RUN=1` logs ops instead of broadcasting).
2. **`record.py`** — `CardRecord` models, `from_scan_response()`, `build_tags()`, `card_permlink()`.
3. **`post_builder.py`** — markdown title/body + json_metadata envelope + decline-payout ops pair.
4. **`images.py`** — sign challenge `sha256(b'ImageSigningChallenge' + bytes)` with posting key; POST multipart field `file` to `https://images.hive.blog/{account}/{sig}`; fallback field `image` + Bearer to images.3speak.tv. Reject non-JPEG/PNG/WebP and >5 MB (images are permanent, no delete API).
5. **`queue.py`** — file-backed `PublishJob` queue + single worker task started via FastAPI lifespan in `main.py`. Loop: FIFO → spacing (305s creates / 15s updates) → RC gate (park if < 5%) → idempotency check (`get_post` on permlink; matching record_id ⇒ confirmed without broadcasting) → broadcast once → on exception verify-on-chain before counting a failure → backoff 1m/5m/30m, failed after 5 → on success poll ~3s until Hivemind indexes, mark confirmed with peakd URL.

**`server/app/config.py`** additions (mirror the existing `ebay_configured` pattern; key never logged, same discipline as `X-AI-Key`): `hive_account`, `hive_posting_key`, `hive_community="hive-192941"`, `hive_nodes`, `hive_dry_run`, `hive_queue_dir`, `hive_root_post_interval_seconds=305`, `hive_min_rc_percent=5.0`, `images_3speak_token`, `hive_configured` property. Update `.env.example`; gitignore `server/data/`.

**New router `server/app/publish_routes.py`** (included from `main.py`):
- `POST /api/publish` — multipart (record JSON + front/back image files) → upload images → enqueue → 202 `{job_id, permlink, position, eta_seconds}`. Idempotent on `record_id`. 503 when Hive unconfigured.
- `GET /api/publish/{job_id}` — job status.
- `GET /api/cards` — proxies `bridge.get_ranked_posts {sort:'created', tag:'hive-192941'}` with cursor pagination, keeps only posts whose json_metadata parses as `card.v==1`, 60s TTL cache (first page invalidated on confirmed publish).
- `GET /api/cards/{permlink}` — `bridge.get_post` → parsed CardRecord.
- `POST /api/cards/{permlink}/refresh-comps` — re-runs existing `scan.py`/`comps.py`/`verdict.py` helpers on the stored `identity.search_string`, enqueues an `update` (edit) job.
- `GET /api/hive/status` — `{configured, account, dry_run, rc_percent, queue_depth, eta_seconds}`.

## Client changes

1. **`web/src/binderDb.ts`** (new, `idb` dep) — IndexedDB `cardscanner`: store `cards` (StagedCard: record_id, ScanResponse, askingPrice, status draft→queued→publishing→published/failed, permlink, job_id) and `images` (prepared JPEG blobs per side, from existing `imagePrep.ts` output). One-time migration of localStorage `cardscanner.history` (legacy entries have no images → viewable but not publishable). History cap 500; never prune published. `clientId()` = uuid in localStorage.
2. **`web/src/binderTypes.ts`** (new) — mirrors `record.py`.
3. **`web/src/binderApi.ts`** (new) — `publishCard`, `getPublishStatus`, `listBinder`, `getBinderCard`, `refreshComps`, `hiveStatus` (style of existing `api.ts`).
4. **`web/src/App.tsx`** — `handleScan` stages scan + prepared blobs via `stageScan()` instead of `pushHistory` (localStorage fallback kept).
5. **`web/src/screens/HistoryScreen.tsx`** — status chips + "Publish to The Binder" button with explicit *public & permanent* consent dialog; `usePublishPoller` hook (30s) shows queue position/ETA; offline re-submit sweep on `online` event (safe — server idempotent on record_id).
6. **`web/src/screens/BinderScreen.tsx`** (new) + nav tab — paginated community feed (cursor infinite scroll), client-side search on player/set/year, detail view adapting `ResultsScreen` + CDN images + Snapie/PeakD links + "Refresh comps".

## Setup / operations (docs: new `docs/hive-setup.md` + DEPLOY.md section)

1. Provision app Hive account; put **posting key only** in `.env` (`HIVE_ACCOUNT`, `HIVE_POSTING_KEY`). ~10–15 HP powered up/delegated covers RC for steady posting.
2. `server/scripts/hive_setup.py` (new, manual): subscribe app account to hive-192941 (`custom_json id='community' ['subscribe',…]`), print RC%, optional `--post-test`.
3. Community props (title "The Binder", description) require owner/admin **@meno** to run `updateProps` — coordinate; optionally get the app account a member/mod role. Not a code task.

## Testing

- **Server (pytest, existing conventions)**: `test_hive_record.py` (tags/permlink/size<8KB using `fixtures/vision_luka_good.json`), `test_hive_post_builder.py` (first-tag rule, decline payout), `test_hive_client.py` (failover via `httpx.MockTransport`, dry-run), `test_hive_images.py` (challenge vector, field names, fallback), `test_publish_queue.py` (fake clock: spacing, restart persistence, broadcast-called-once assertion, RC park), `test_publish_endpoints.py`, `test_cards_endpoints.py` (fixture with card + human + malformed posts → filtering/pagination).
- **Web (vitest + `fake-indexeddb`)**: `binderDb.test.ts` (migration, prune rules), `binderApi.test.ts`, screen tests for chips/consent/pagination.
- **No testnet dependency**: mock transports + `HIVE_DRY_RUN=1` for end-to-end dev runs.
- **Manual verification**: publish one real card → confirm it renders at `peakd.com/c/hive-192941` and snapie.io, image loads from images.hive.blog, record round-trips through `GET /api/cards`; run `make test` (server + web suites).

## Implementation order (TDD)

1. Config + lighthive dep + `hive/client.py`
2. `hive/record.py` + `hive/post_builder.py` (pure functions)
3. `hive/images.py`
4. `hive/queue.py` + publish endpoints + lifespan wiring
5. Read endpoints (`/api/cards…`)
6. `binderTypes.ts` + `binderDb.ts` + App.tsx staging rewire
7. `binderApi.ts` + HistoryScreen publish UI + poller
8. BinderScreen browse UI
9. refresh-comps update path
10. `hive_setup.py` script + docs + design doc `docs/plans/2026-08-16-hive-binder-design.md`

## Risks (accepted)

- **Public forever**: published cards (images, grades, asking prices) are permanent on a public chain/CDN; no image deletion exists. Mitigation: opt-in per card with explicit consent copy; attribution is an anonymous UUID.
- **Throughput ceiling**: 1 root post/5 min ≈ 288 cards/day on one account; UI shows honest queue ETAs; comment-anchor escape hatch documented.
- **Posting key compromise** = spam risk only (not funds); env-only, never logged, rotatable.
- **Single-process queue**: multiple server replicas would race; permlink idempotency is the backstop.
- **Moderation**: community mods can mute posts from the feed view — coordinate with @meno up front; declining rewards keeps it clean.
