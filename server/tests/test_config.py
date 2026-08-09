from app.config import Settings


def test_defaults_allow_missing_ebay(monkeypatch):
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    s = Settings(_env_file=None)
    assert s.ebay_configured is False


def test_ebay_configured(monkeypatch):
    s = Settings(_env_file=None, ebay_client_id="x", ebay_client_secret="y")
    assert s.ebay_configured is True
