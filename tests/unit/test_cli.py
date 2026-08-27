from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
import typer
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from typer.testing import CliRunner

from app import cli as cli_module

runner = CliRunner()


def make_app():
    app = typer.Typer()
    app.command()(cli_module.main)
    return app


@pytest.fixture
def fake_page():
    page = MagicMock()
    page.url = "http://localhost:5000/dashboard"
    fake_download = MagicMock()
    fake_download.suggested_filename = "report.txt"
    page.expect_download.return_value.__enter__.return_value.value = fake_download
    return page


@pytest.fixture
def fake_playwright(monkeypatch, fake_page):
    fake_browser = MagicMock()
    fake_browser.new_page.return_value = fake_page
    fake_p = MagicMock()
    fake_p.chromium.launch.return_value = fake_browser

    @contextmanager
    def fake_sync_playwright():
        yield fake_p

    monkeypatch.setattr(cli_module, "sync_playwright", fake_sync_playwright)
    return fake_p


@pytest.fixture(autouse=True)
def isolated_download_dir(monkeypatch, tmp_path):
    """Prevent any test from writing into the real repo's downloads/ folder."""
    monkeypatch.setattr(cli_module, "DOWNLOAD_DIR", tmp_path / "downloads")


def test_unknown_site_raises_error(fake_playwright):
    result = runner.invoke(make_app(), ["--site", "nope"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ValueError)
    assert "Unknown site 'nope'" in str(result.exception)


def test_missing_username_raises_error(fake_playwright, monkeypatch):
    monkeypatch.delenv("PORTAL_USERNAME", raising=False)
    result = runner.invoke(make_app(), ["--site", "demo_portal"])
    assert result.exit_code != 0
    assert isinstance(result.exception, EnvironmentError)


def test_missing_password_raises_error(fake_playwright, monkeypatch):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.delenv("PORTAL_PASSWORD", raising=False)
    result = runner.invoke(make_app(), ["--site", "demo_portal"])
    assert result.exit_code != 0
    assert isinstance(result.exception, EnvironmentError)


def test_successful_login_downloads_report(fake_playwright, monkeypatch):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "demo123")
    page = fake_playwright.chromium.launch.return_value.new_page.return_value

    result = runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    assert result.exit_code == 0
    page.fill.assert_any_call("#username", "demo")
    page.fill.assert_any_call("#password", "demo123")
    page.wait_for_url.assert_called_once_with("**/dashboard", timeout=3000)
    page.click.assert_any_call('a[href="/download"]')
    downloaded = page.expect_download.return_value.__enter__.return_value.value
    downloaded.save_as.assert_called_once_with(cli_module.DOWNLOAD_DIR / "report.txt")


def test_login_failure_sends_slack_notification(fake_playwright, monkeypatch):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "wrong")
    page = fake_playwright.chromium.launch.return_value.new_page.return_value
    page.wait_for_url.side_effect = PlaywrightTimeoutError("timeout")

    mock_notify = MagicMock()
    monkeypatch.setattr(cli_module, "notify_slack", mock_notify)

    result = runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    assert result.exit_code == 0
    mock_notify.assert_called_once()
    assert "demo_portal" in mock_notify.call_args[0][0]


def test_display_browser_flag_controls_headless(fake_playwright, monkeypatch):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "demo123")

    runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])
    fake_playwright.chromium.launch.assert_called_once_with(headless=True)


def test_display_browser_flag_defaults_to_visible(fake_playwright, monkeypatch):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "demo123")

    runner.invoke(make_app(), ["--site", "demo_portal"])
    fake_playwright.chromium.launch.assert_called_once_with(headless=False)
