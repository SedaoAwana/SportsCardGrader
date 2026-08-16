from app.config import Settings


def test_defaults_allow_missing_ebay(monkeypatch):
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    s = Settings(_env_file=None)
    assert s.ebay_configured is False


def test_ebay_configured(monkeypatch):
    s = Settings(_env_file=None, ebay_client_id="x", ebay_client_secret="y")
    assert s.ebay_configured is True


def test_defaults_allow_missing_hive():
    s = Settings(_env_file=None)
    assert s.hive_configured is False
    assert s.hive_community == "hive-192941"
    assert s.hive_dry_run is False
    assert s.hive_root_post_interval_seconds == 305
    assert s.hive_min_rc_percent == 5.0
    assert s.hive_queue_dir == "data/publish_queue"


def test_hive_configured():
    s = Settings(_env_file=None, hive_account="thebinder", hive_posting_key="5J...")
    assert s.hive_configured is True


def test_hive_node_list_default_and_override():
    assert len(Settings(_env_file=None).hive_node_list) >= 3
    s = Settings(_env_file=None, hive_nodes="https://a.example, https://b.example")
    assert s.hive_node_list == ["https://a.example", "https://b.example"]
