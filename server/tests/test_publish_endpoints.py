import io
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.hive.queue import PublishQueue
from app.main import app
from app.publish_routes import HiveState
from tests.test_hive_record import COMMUNITY, make_record
from tests.test_publish_queue import FakeClock, FakeHive

JPEG = b"\xff\xd8\xff\xe0" + b"x" * 32


@pytest.fixture
def client_unconfigured():
    app.state.hive = None
    return TestClient(app)


@pytest.fixture
def hive():
    return FakeHive()


@pytest.fixture
def client(tmp_path, hive):
    async def instant_sleep(_):
        pass

    async def image_host(request):
        if request.url.host == "images.hive.blog":
            return httpx.Response(200, json={"url": f"https://images.hive.blog/DQm/{request.url.path.split('/')[-1][:6]}.jpg"})
        raise AssertionError(f"unexpected host {request.url.host}")

    queue = PublishQueue(tmp_path, hive, COMMUNITY, clock=FakeClock(),
                         sleeper=instant_sleep)
    app.state.hive = HiveState(
        client=hive, queue=queue, community=COMMUNITY,
        http=httpx.AsyncClient(transport=httpx.MockTransport(image_host)),
        # Any valid WIF works for signing in tests.
        posting_key="5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3",
        fallback_token="", dry_run=False,
    )
    yield TestClient(app)
    app.state.hive = None


def draft_json(record_id="4fef9db2-9f3a-4c5e-8f6d-0123456789ab") -> str:
    record = make_record(record_id=record_id)
    data = json.loads(record.model_dump_json(exclude={"images"}))
    return json.dumps(data)


def post_publish(client, record=None, record_id="4fef9db2-9f3a-4c5e-8f6d-0123456789ab",
                 front=JPEG):
    return client.post("/api/publish", data={"record": record or draft_json(record_id)},
                       files={"front": ("front.jpg", io.BytesIO(front), "image/jpeg")})


def test_publish_503_when_unconfigured(client_unconfigured):
    resp = post_publish(client_unconfigured)
    assert resp.status_code == 503


def test_publish_happy_path(client):
    resp = post_publish(client)
    assert resp.status_code == 202
    body = resp.json()
    assert body["permlink"].startswith("card-luka-doncic-2018-")
    assert body["status"] == "queued"
    assert body["position"] == 1
    assert body["eta_seconds"] >= 0


def test_publish_idempotent_on_record_id(client):
    first = post_publish(client).json()
    resp = post_publish(client)
    assert resp.status_code == 200
    assert resp.json()["job_id"] == first["job_id"]


def test_publish_rejects_bad_record_json(client):
    resp = post_publish(client, record="{not json")
    assert resp.status_code == 422


def test_publish_rejects_bad_image(client):
    resp = post_publish(client, front=b"GIF89a not an allowed type")
    assert resp.status_code == 422


def test_job_status_roundtrip(client):
    job_id = post_publish(client).json()["job_id"]
    resp = client.get(f"/api/publish/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"
    assert client.get("/api/publish/nope").status_code == 404


def test_dry_run_skips_image_upload(client):
    # A dry-run rehearsal must not push permanent bytes to the real CDN.
    state = app.state.hive
    state.dry_run = True
    state.http = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: (_ for _ in ()).throw(AssertionError("network used in dry run"))))
    resp = post_publish(client)
    assert resp.status_code == 202
    job = state.queue.get_job(resp.json()["job_id"])
    assert job.record.images.front.startswith("dry-run://")


def test_hive_status_unconfigured(client_unconfigured):
    body = client_unconfigured.get("/api/hive/status").json()
    assert body == {"configured": False}


def test_hive_status_configured(client):
    body = client.get("/api/hive/status").json()
    assert body["configured"] is True
    assert body["community"] == COMMUNITY
    assert body["rc_percent"] == 80.0
    assert body["queue_depth"] == 0
