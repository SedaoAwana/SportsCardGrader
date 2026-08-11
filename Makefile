.PHONY: setup dev server web test

# One-time setup: Python venv + server deps, web deps.
setup:
	cd server && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
	cd web && npm install

# Run the API server on :8000.
# The server reads eBay credentials from the environment; this target sources
# the repo-root .env (if present) before starting uvicorn, so you only ever
# maintain one .env at the repo root.
server:
	cd server && set -a; [ -f ../.env ] && . ../.env; set +a; .venv/bin/uvicorn app.main:app --reload --port 8000

# Run the web dev server on :5173 (proxies /api to :8000 — see web/vite.config.ts).
web:
	cd web && npm run dev

# Run both at once.
dev:
	$(MAKE) -j2 server web

test:
	cd server && .venv/bin/pytest -q
	cd web && npm test
