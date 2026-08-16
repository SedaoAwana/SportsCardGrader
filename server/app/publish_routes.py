"""Publish cards to The Binder community and read them back.

All Hive machinery hangs off app.state.hive (a HiveState); when Hive is not
configured the app still runs fully — these endpoints just answer 503.
"""
import logging
from dataclasses import dataclass, field
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.hive.client import HiveClient
from app.hive.images import ImageInvalid, ImageUploadError, upload_image
from app.hive.queue import PublishJob, PublishQueue
from app.hive.record import CardImages, CardRecord, CardRecordDraft

logger = logging.getLogger(__name__)

router = APIRouter()


@dataclass
class HiveState:
    client: HiveClient
    queue: PublishQueue
    community: str
    http: httpx.AsyncClient
    posting_key: str = field(repr=False, default="")  # never in logs/repr
    fallback_token: str = field(repr=False, default="")
    dry_run: bool = False


def _state(request: Request) -> HiveState:
    state = getattr(request.app.state, "hive", None)
    if state is None:
        raise HTTPException(503, "Publishing is not configured on this server.")
    return state


def _job_payload(job: PublishJob, queue: PublishQueue) -> dict:
    return {
        "job_id": job.job_id,
        "permlink": job.permlink,
        "status": job.status,
        "position": queue.position(job.job_id),
        "eta_seconds": queue.eta_for(job.job_id),
        "hive_url": job.hive_url,
        "last_error": job.last_error,
    }


@router.post("/api/publish", status_code=202)
async def publish(
    request: Request,
    record: Annotated[str, Form()],
    front: Annotated[UploadFile, File()],
    back: Annotated[Optional[UploadFile], File()] = None,
):
    state = _state(request)
    try:
        draft = CardRecordDraft.model_validate_json(record)
    except ValidationError as exc:
        raise HTTPException(422, f"Invalid card record: {exc.errors()[0]['msg']}")

    existing = state.queue.get_job(draft.record_id)
    if existing is not None:
        # Idempotent re-submit (offline retry, double tap): same job back.
        return JSONResponse(status_code=200,
                            content=_job_payload(existing, state.queue))

    async def _upload(upload: UploadFile) -> str:
        try:
            return await upload_image(
                await upload.read(), upload.filename or "card.jpg",
                account=state.client.account, posting_key=state.posting_key,
                http=state.http, fallback_token=state.fallback_token)
        except ImageInvalid as exc:
            raise HTTPException(422, str(exc))
        except ImageUploadError as exc:
            raise HTTPException(502, str(exc))

    images = CardImages(front=await _upload(front),
                        back=await _upload(back) if back is not None else None)
    full = CardRecord(**draft.model_dump(), images=images)
    job = state.queue.enqueue(full)
    return _job_payload(job, state.queue)


@router.get("/api/publish/{job_id}")
async def publish_status(request: Request, job_id: str):
    state = _state(request)
    job = state.queue.get_job(job_id)
    if job is None:
        raise HTTPException(404, "Unknown publish job.")
    return _job_payload(job, state.queue)


@router.get("/api/hive/status")
async def hive_status(request: Request):
    state = getattr(request.app.state, "hive", None)
    if state is None:
        return {"configured": False}
    try:
        rc_percent = await state.client.get_rc_percent()
    except Exception:  # noqa: BLE001 — status must not 500 on node flakiness
        rc_percent = None
    queue_status = state.queue.status()
    return {
        "configured": True,
        "account": state.client.account,
        "community": state.community,
        "dry_run": state.dry_run,
        "rc_percent": rc_percent,
        "queue_depth": queue_status["depth"],
        "eta_seconds": queue_status["eta_seconds"],
    }
