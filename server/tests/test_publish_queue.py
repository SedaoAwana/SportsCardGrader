import json

import pytest

from app.hive.queue import MAX_ATTEMPTS, PublishJob, PublishQueue
from tests.test_hive_record import COMMUNITY, make_record


class FakeClock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now


class FakeHive:
    """Chain double: get_post reflects what broadcast_ops 'published'."""

    def __init__(self):
        self.account = "thebinder"
        self.posts: dict[str, dict] = {}
        self.broadcast_calls = 0
        self.rc = 80.0
        self.fail_broadcast: Exception | None = None
        self.swallow_broadcast = False  # error raised but the post DID land

    async def get_post(self, author, permlink):
        return self.posts.get(permlink)

    async def get_rc_percent(self):
        return self.rc

    async def broadcast_ops(self, ops):
        self.broadcast_calls += 1
        if self.fail_broadcast is not None:
            if self.swallow_broadcast:
                self._land(ops)
            raise self.fail_broadcast
        self._land(ops)
        return "txid"

    def _land(self, ops):
        comment = ops[0][1]
        self.posts[comment["permlink"]] = {
            "author": comment["author"],
            "permlink": comment["permlink"],
            "json_metadata": json.loads(comment["json_metadata"]),
        }


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def hive():
    return FakeHive()


@pytest.fixture
def queue(tmp_path, hive, clock):
    return make_queue(tmp_path, hive, clock)


def make_queue(tmp_path, hive, clock):
    async def instant_sleep(seconds):
        clock.now += seconds

    return PublishQueue(tmp_path, hive, COMMUNITY, root_interval=305.0,
                        update_interval=15.0, min_rc_percent=5.0,
                        clock=clock, sleeper=instant_sleep)


def test_enqueue_is_idempotent_on_record_id(queue):
    record = make_record()
    job1 = queue.enqueue(record)
    job2 = queue.enqueue(record)
    assert job1.job_id == job2.job_id == record.record_id
    assert queue.status()["depth"] == 1


async def test_create_publishes_and_confirms(queue, hive):
    job = queue.enqueue(make_record())
    await queue.tick()
    refreshed = queue.get_job(job.job_id)
    assert refreshed.status == "confirmed"
    assert hive.broadcast_calls == 1
    assert refreshed.hive_url == f"https://peakd.com/@thebinder/{job.permlink}"


async def test_root_post_spacing_enforced(queue, hive, clock):
    queue.enqueue(make_record(record_id="one"))
    queue.enqueue(make_record(record_id="two"))
    await queue.tick()
    assert hive.broadcast_calls == 1
    delay = await queue.tick()  # too soon for a second root post
    assert hive.broadcast_calls == 1
    assert delay > 0
    clock.now += delay
    await queue.tick()
    assert hive.broadcast_calls == 2


async def test_already_on_chain_confirms_without_broadcast(queue, hive):
    record = make_record()
    job = queue.enqueue(record)
    # Simulate a restart that lost the confirmation but the post landed.
    hive.posts[job.permlink] = {
        "author": "thebinder", "permlink": job.permlink,
        "json_metadata": {"card": {"record_id": record.record_id}},
    }
    await queue.tick()
    assert queue.get_job(job.job_id).status == "confirmed"
    assert hive.broadcast_calls == 0


async def test_broadcast_error_but_post_landed_never_rebroadcasts(queue, hive):
    hive.fail_broadcast = RuntimeError("socket dropped mid-broadcast")
    hive.swallow_broadcast = True
    job = queue.enqueue(make_record())
    await queue.tick()
    assert queue.get_job(job.job_id).status == "confirmed"
    assert hive.broadcast_calls == 1  # the iron rule: at most one broadcast


async def test_broadcast_error_backs_off_then_fails(queue, hive, clock):
    hive.fail_broadcast = RuntimeError("node rejected")
    job = queue.enqueue(make_record())
    for attempt in range(1, MAX_ATTEMPTS + 1):
        delay = await queue.tick()
        refreshed = queue.get_job(job.job_id)
        assert refreshed.attempts == attempt
        if attempt < MAX_ATTEMPTS:
            assert refreshed.status == "queued"
            clock.now += delay
        else:
            assert refreshed.status == "failed"
    assert "node rejected" in queue.get_job(job.job_id).last_error


async def test_low_rc_parks_queue(queue, hive):
    hive.rc = 1.0
    job = queue.enqueue(make_record())
    delay = await queue.tick()
    assert hive.broadcast_calls == 0
    assert queue.get_job(job.job_id).status == "queued"
    assert "Resource Credits" in queue.get_job(job.job_id).last_error
    assert delay >= 300


async def test_updates_use_short_spacing(queue, hive):
    queue.enqueue(make_record(record_id="a"))
    await queue.tick()  # create confirmed; root cooldown now active
    queue.enqueue(make_record(record_id="b"), kind="update")
    await queue.tick()
    assert hive.broadcast_calls == 2  # edit not blocked by the 5-min root gap


async def test_restart_persistence(tmp_path, hive, clock):
    q1 = make_queue(tmp_path, hive, clock)
    record = make_record()
    q1.enqueue(record)
    q1.enqueue(make_record(record_id="second"))
    await q1.tick()

    q2 = make_queue(tmp_path, hive, clock)  # simulated restart, same dir
    assert q2.get_job(record.record_id).status == "confirmed"
    assert q2.status()["depth"] == 1
    delay = await q2.tick()  # root cooldown survives restart too
    assert hive.broadcast_calls == 1 and delay > 0


def test_status_reports_eta(queue):
    queue.enqueue(make_record(record_id="a"))
    queue.enqueue(make_record(record_id="b"))
    status = queue.status()
    assert status["depth"] == 2
    assert status["eta_seconds"] >= 305
    assert queue.position("b") == 2
