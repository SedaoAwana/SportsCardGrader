import json

from app.hive.post_builder import build_post
from app.hive.record import card_permlink
from app.schemas import Slab
from tests.test_hive_record import COMMUNITY, make_record

ACCOUNT = "thebinder"


def build(record):
    return build_post(record, community=COMMUNITY, account=ACCOUNT,
                      permlink=card_permlink(record))


def test_comment_op_shape():
    record = make_record()
    ops = build(record)
    assert [name for name, _ in ops] == ["comment", "comment_options"]
    comment = ops[0][1]
    assert comment["parent_author"] == ""
    assert comment["parent_permlink"] == COMMUNITY
    assert comment["author"] == ACCOUNT
    assert comment["permlink"] == card_permlink(record)
    assert "Luka Doncic" in comment["title"] and len(comment["title"]) <= 255


def test_json_metadata_envelope():
    record = make_record()
    meta = json.loads(build(record)[0][1]["json_metadata"])
    assert meta["app"].startswith("cardscanner/")
    assert meta["tags"][0] == COMMUNITY
    assert meta["image"] == [record.images.front]
    assert meta["card"]["record_id"] == record.record_id
    assert meta["card"]["v"] == 1
    assert len(json.dumps(meta)) < 8192


def test_body_is_browsable_markdown():
    record = make_record()
    body = build(record)[0][1]["body"]
    assert record.images.front in body
    assert "Luka Doncic" in body and "Panini Prizm" in body
    assert "$47" in body  # comps median surfaces in the summary line


def test_slab_title_variant():
    record = make_record(slab=Slab(company="PSA", grade="9"), condition=None)
    title = build(record)[0][1]["title"]
    assert "PSA 9" in title


def test_payout_declined():
    options = build(make_record())[1][1]
    assert options["max_accepted_payout"] == "0.000 HBD"
    assert options["author"] == ACCOUNT
    assert options["allow_votes"] is True
    assert options["allow_curation_rewards"] is True
    assert options["extensions"] == []
