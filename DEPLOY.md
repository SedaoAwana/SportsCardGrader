# Deploying Card Scanner

Two pieces: the FastAPI server (`server/`) and the static web app (`web/dist`). The server is stateless — no database, no volumes — so any container host works.

## 1. Deploy the server (Fly.io or Railway)

> **Request timeout:** a scan holds the request open for the whole AI pipeline.
> The server self-limits at 55 seconds, so the platform/load-balancer request
> timeout must exceed **60 seconds** — otherwise the LB cuts the scan mid-flight
> and the client sees a generic gateway error instead of the server's 504.
> (Fly.io and Railway defaults are fine; check `idle_timeout`/proxy settings if
> you front the server with your own nginx/ALB.)

The server just needs Python 3.12 and this start command:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> **Hive publishing (optional):** set `HIVE_ACCOUNT` and `HIVE_POSTING_KEY`
> (posting key only) to enable publishing to The Binder — see
> [`docs/hive-setup.md`](docs/hive-setup.md). The publish queue persists to
> `data/publish_queue/` on local disk, so give the server a persistent volume
> and run a SINGLE instance — replicas would double-post to the chain.

### Fly.io

```bash
cd server
fly launch --no-deploy        # generates fly.toml; pick a name/region
fly secrets set EBAY_CLIENT_ID=... EBAY_CLIENT_SECRET=...
fly deploy
```

If `fly launch` doesn't detect the app, use a minimal Dockerfile in `server/`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Railway

1. New project → Deploy from GitHub repo, set the root directory to `server/`.
2. Build: `pip install .` — Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Add variables `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`.

The eBay variables are optional — without them scans work but have no market prices.

## 2. Build and host the web app

Build with the API URL baked in:

```bash
cd web
VITE_API_URL=https://your-server.fly.dev npm run build
```

Then host `web/dist` on any static host — Netlify, Vercel, Cloudflare Pages, GitHub Pages. It's plain static files; no server-side rendering, no functions.

Example (Netlify CLI):

```bash
npx netlify deploy --prod --dir=dist
```

## Alternative: one service

You can skip the static host and serve the built web app from FastAPI itself. Build the web app **without** `VITE_API_URL` (same-origin), copy `web/dist` into the server image, and add to `server/app/main.py`:

```python
from fastapi.staticfiles import StaticFiles

# after all /api routes are registered:
app.mount("/", StaticFiles(directory="dist", html=True), name="web")
```

One deploy, one URL, no CORS concerns. The tradeoff: web-only changes require redeploying the server.
