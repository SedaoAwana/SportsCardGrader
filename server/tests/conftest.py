"""Shared test hygiene: pricing-source and settings state must never leak
between test files (the scan module holds a lazy process-wide singleton)."""

import pytest

from app import scan as scan_module
from app.config import get_settings


@pytest.fixture(autouse=True)
def _reset_pricing_state():
    scan_module._pricing_source = None
    get_settings.cache_clear()
    yield
    scan_module._pricing_source = None
    get_settings.cache_clear()
