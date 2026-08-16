# Hive Binder Storage — Implementation Plan (v1)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Persist scanned cards (images, metadata, comps) by publishing them as posts to Hive community `hive-192941` ("The Binder"), with client-side IndexedDB staging and a central app account signing — no conventional database.

**Architecture:** Client stages scans + prepared image blobs in IndexedDB. `POST /api/publish` uploads images to images.hive.blog and enqueues a file-backed publish job; a single lifespan worker broadcasts one root post per ~5 min via lighthive with node failover, deterministic permlinks, and verify-before-retry. Reads proxy Hivemind `bridge` calls. Full design: `2026-08-16-hive-binder-design.md`.

**Tech Stack:** FastAPI + httpx + lighthive (server), React 19 + `idb` (web), pytest + `httpx.MockTransport`, vitest + `fake-indexeddb`.

Each task is TDD: write failing tests → run (`cd server && .venv/bin/pytest tests/<file> -q` or `cd web && npx vitest run <file>`) → implement minimally → tests pass → commit.

---

### Task 1: Hive config
- Modify: `server/app/config.py` — add `hive_account`, `hive_posting_key`, `hive_community="hive-192941"`, `hive_nodes` (comma-sep, empty = defaults), `hive_dry_run=False`, `hive_queue_dir="data/publish_queue"`, `hive_root_post_interval_seconds=305`, `hive_min_rc_percent=5.0`, `images_3speak_token`, property `hive_configured`.
- Modify: `server/tests/test_config.py`, `.env.example`, `.gitignore` (add `server/data/`).
- Add `lighthive>=0.4` to `server/pyproject.toml`; `cd server && .venv/bin/pip install -e ".[dev]"`.
- Commit: `feat(server): hive settings`

### Task 2: RPC client with failover (`server/app/hive/client.py`)
- Create: `server/app/hive/__init__.py`, `client.py`; Test: `server/tests/test_hive_client.py` (uses `httpx.MockTransport`).
- `DEFAULT_NODES` list; `class HiveClient(nodes, account, posting_key, dry_run, transport=None)`.
- `async call(api, method, params)`: JSON-RPC 2.0 POST; on transport error / non-200 / JSON-RPC error → next node; remember last-good node; `HiveUnavailable` after all fail.
- `async get_post(author, permlink) -> dict|None` (bridge.get_post; JSON-RPC "does not exist" error → None, confirmed on a second node).
- `async get_ranked_posts(sort, tag, limit, start_author, start_permlink) -> list`.
- `async get_rc_percent() -> float` (rc_api.find_rc_accounts: rc_manabar.current_mana / max_rc * 100).
- `async broadcast_ops(ops) -> str`: dry_run → log + return `"dry-run"`; else lighthive `Client(nodes).broadcast()` via `asyncio.to_thread`. Called at most once per attempt (caller contract).
- Commit: `feat(server): hive rpc client with node failover`

### Task 3: Card record + tags + permlink (`server/app/hive/record.py`)
- Create: `record.py`; Test: `server/tests/test_hive_record.py` (fixture `vision_luka_good.json`).
- Models: `CardComps` (summary, top_sales ≤10, titles ≤80 chars, as_of), `CardImages`, `Attribution`, `CardRecord` (v=1, kind="card", record_id, identity/condition/slab/authenticity/verdict from existing schemas, comps, images, asking_price, attribution, scanned_at), `CardRecordDraft` (= record minus images).
- `slugify(s, max_len)`; `build_tags(identity, community) -> ["hive-192941","sportscards","cardscanner","sc-<player>","sc-<year>","sc-<set≤24>"]` (≤8, lowercase `[a-z][a-z0-9-]*`, dedup).
- `card_permlink(record)` = `card-{player-slug≤32}-{year}-{sha256(record_id)[:8]}`, charset `[a-z0-9-]`.
- Commit: `feat(server): canonical hive card record`

### Task 4: Post builder (`server/app/hive/post_builder.py`)
- Create: `post_builder.py`; Test: `server/tests/test_hive_post_builder.py`.
- `build_post(record, community, account, permlink) -> list[ops]`: `comment` op (parent_author "", parent_permlink=community, markdown body with images/stats table/comps line/footer, title ≤255) + `comment_options` op declining payout (`max_accepted_payout "0.000 HBD"`, `percent_hbd 10000`, allow_votes True, allow_curation_rewards True, no extensions).
- json_metadata: `{app:"cardscanner/1.0", format:"markdown", tags (first = community), image:[...], description, card:{...}}`; serialized size < 8192 asserted in tests with maximal record.
- Commit: `feat(server): hive post builder with declined payout`

### Task 5: Image upload (`server/app/hive/images.py`)
- Create: `images.py`; Test: `server/tests/test_hive_images.py`.
- `sign_image_challenge(data, wif) -> str`: sha256(b"ImageSigningChallenge"+data), lighthive PrivateKey ECDSA recoverable-compact hex.
- `async upload_image(data, filename, account, posting_key, http) -> url`: POST multipart field `file` to `https://images.hive.blog/{account}/{sig}`; on failure → 3speak fallback (field `image`, Bearer token) if configured; else `ImageUploadError`. Reject non-JPEG/PNG/WebP or >5 MB before upload.
- Commit: `feat(server): images.hive.blog upload with fallback`

### Task 6: Publish queue (`server/app/hive/queue.py`)
- Create: `queue.py`; Test: `server/tests/test_publish_queue.py` (fake clock + fake HiveClient; assert broadcast call count == 1 on error path; restart persistence by re-instantiating over same tmp dir).
- `PublishJob` (job_id=record_id, kind create|update, record, permlink, status queued|publishing|confirmed|failed, attempts, last_error, enqueued_at, confirmed_at, hive_url); one JSON file per job, atomic tmp+rename.
- `PublishQueue.enqueue(record, kind)` idempotent; `get_job`, `status()` (depth, eta_seconds, last_published_at).
- Worker loop: oldest queued → spacing (305s create / 15s update since last confirmed create) → RC gate (<5% parks, retry 10 min) → idempotency `get_post` check (existing + matching record_id ⇒ confirmed, no broadcast) → build ops → broadcast once → exception: sleep ~9s, re-check chain; found ⇒ confirmed, else attempts++ backoff 60s/300s/1800s, failed at 5 → success: poll get_post ≤4× @3s, confirmed + `hive_url`.
- Commit: `feat(server): file-backed hive publish queue`

### Task 7: Publish endpoints + lifespan (`server/app/publish_routes.py`)
- Create: `publish_routes.py`; Modify: `server/app/main.py` (lifespan starts/stops worker when `hive_configured`, include router). Test: `server/tests/test_publish_endpoints.py`.
- `POST /api/publish` (multipart record JSON + front + optional back): 503 unconfigured; validate `CardRecordDraft`; upload images; enqueue; 202 `{job_id, permlink, status, position, eta_seconds}`; duplicate record_id → 200 existing job. Image limits: JPEG/PNG/WebP, ≤5 MB.
- `GET /api/publish/{job_id}` → job status or 404. `GET /api/hive/status` → `{configured, account, community, dry_run, rc_percent, queue_depth, eta_seconds}`.
- Commit: `feat(server): publish endpoints and queue lifespan`

### Task 8: Read endpoints (cards feed)
- Modify: `publish_routes.py` (or `cards_routes.py`); Test: `server/tests/test_cards_endpoints.py` + fixture `server/tests/fixtures/bridge_ranked_posts.json` (card post, human post, malformed metadata).
- `GET /api/cards?limit&start_author&start_permlink`: bridge.get_ranked_posts sort=created tag=community; keep posts parsing as `card.v==1` (default author==app account; `all_authors=1` relaxes); → `{cards:[{permlink,author,created,card}], next}`; 60s TTL cache keyed by cursor, first page invalidated on confirmed publish.
- `GET /api/cards/{permlink}` → parsed card or 404.
- Commit: `feat(server): community feed read endpoints`

### Task 9: Client staging (`web/src/binderDb.ts`, `binderTypes.ts`)
- Create: `web/src/binderTypes.ts` (mirror record.py), `web/src/binderDb.ts`; Test: `web/src/binderDb.test.ts` (`fake-indexeddb` dev-dep); `npm i idb && npm i -D fake-indexeddb`.
- IDB `cardscanner` v1: store `cards` (keyPath record_id: at, response, askingPrice?, status draft|queued|publishing|published|failed, publishRequested?, permlink?, hive_url?, job_id?, error?, legacy?), store `images` (keyPath [record_id, side], blob).
- `stageScan(response, askingPrice, front, back)`, `listStaged()`, `getImages(id)`, `setStatus(id, patch)`, `deleteStaged(id)`, `migrateFromLocalStorage()` (history entries → draft, `legacy:true`, no images), cap 500 pruning drafts only; `clientId()` uuid in localStorage `cardscanner.client_id`.
- Commit: `feat(web): indexeddb staging layer`

### Task 10: Stage scans in App
- Modify: `web/src/App.tsx` — after successful scan, `stageScan(...)` with prepFront/prepBack blobs (localStorage `pushHistory` kept as fallback on failure); call `migrateFromLocalStorage()` on app start.
- Test: update `web/src/App.test.tsx`.
- Commit: `feat(web): stage scans with images`

### Task 11: Publish API + HistoryScreen UI
- Create: `web/src/binderApi.ts` (`publishCard`, `getPublishStatus`, `listBinder`, `getBinderCard`, `refreshComps`, `hiveStatus` — style of `api.ts`); Test: `binderApi.test.ts`.
- Modify: `web/src/screens/HistoryScreen.tsx` — rows from `listStaged()`, status chips, "Publish to The Binder" button + public-and-permanent consent dialog, `usePublishPoller` (30s) with position/ETA, offline re-submit sweep (`online` event + start sweep on `publishRequested` drafts). Tests updated.
- Commit: `feat(web): publish to the binder flow`

### Task 12: Binder browse screen
- Create: `web/src/screens/BinderScreen.tsx` + nav tab in `App.tsx`: cursor-paginated feed via `listBinder`, client-side player/set/year filter, detail view (adapt ResultsScreen rendering + CDN images + PeakD/Snapie links + Refresh comps button). Test: `BinderScreen.test.tsx`.
- Commit: `feat(web): binder community feed screen`

### Task 13: Comps refresh (update path)
- Modify: `publish_routes.py` — `POST /api/cards/{permlink}/refresh-comps`: load post, re-run `scan.py` comps helpers + `verdict.decide`, rebuild `comps`/`verdict` with fresh `as_of`, enqueue `kind="update"`. Tests extend queue + endpoints suites.
- Commit: `feat(server): comps refresh via post edit`

### Task 14: Setup script + docs
- Create: `server/scripts/hive_setup.py` (subscribe custom_json to community, print RC%, `--post-test` respecting HIVE_DRY_RUN); `docs/hive-setup.md` (account provisioning, posting key only, ~10–15 HP for RC, @meno must set community title via updateProps); update `README.md`, `DEPLOY.md`.
- Commit: `docs: hive binder setup`

### Verification
1. `make test` — both suites green.
2. `HIVE_DRY_RUN=1` + `make dev`: scan a sample card, publish from History, watch dry-run ops in server log, job reaches confirmed.
3. Real run: set `HIVE_ACCOUNT`/`HIVE_POSTING_KEY`, publish one card, confirm at `https://peakd.com/c/hive-192941` and snapie.io; image loads from images.hive.blog; card appears in Binder tab via `GET /api/cards`.
