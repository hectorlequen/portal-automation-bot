import os

# Set safe defaults before any module under test is imported, since demo_portal.py
# reads FLASK_SECRET_KEY at import time and main.py loads config.yaml at import time.
# setdefault() keeps real .env values if they're already present in the environment.
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")
os.environ.setdefault("PORTAL_USERNAME", "demo")
os.environ.setdefault("PORTAL_PASSWORD", "demo123")

import pytest  # noqa: E402
from tenacity import wait_none  # noqa: E402

import main as main_module  # noqa: E402


@pytest.fixture(autouse=True)
def fast_retries(monkeypatch):
    """Skip tenacity's exponential backoff so retry tests run instantly."""
    monkeypatch.setattr(main_module.PortalBot.check_login_success.retry, "wait", wait_none())
    monkeypatch.setattr(main_module.PortalBot.download_report.retry, "wait", wait_none())
