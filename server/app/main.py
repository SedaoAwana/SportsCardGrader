from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Card Scanner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # public, keyless API surface; the AI key is the user's own
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
