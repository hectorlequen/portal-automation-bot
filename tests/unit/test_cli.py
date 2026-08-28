import logging
from contextlib import contextmanager
from pathlib import Path
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
    fake_download.save_as.side_effect = lambda path: Path(path).touch()
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


@pytest.fixture(autouse=True)
def mock_notify(monkeypatch):
    """Prevent every test from hitting the real SLACK_WEBHOOK_URL / Webhook.site."""
    mock = MagicMock()
    monkeypatch.setattr(cli_module, "notify_slack", mock)
    return mock


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


def test_successful_run_downloads_report_and_exits_zero(fake_playwright, monkeypatch):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "demo123")
    page = fake_playwright.chromium.launch.return_value.new_page.return_value

    result = runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    assert result.exit_code == 0
    page.fill.assert_any_call("#username", "demo")
    page.fill.assert_any_call("#password", "demo123")
    page.wait_for_url.assert_called_once_with("**/dashboard", timeout=3000)
    page.click.assert_any_call('a[href="/download"]')
    assert (cli_module.DOWNLOAD_DIR / "report.txt").exists()


def test_successful_run_logs_each_step(fake_playwright, monkeypatch, caplog):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "demo123")

    with caplog.at_level(logging.INFO):
        result = runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    assert result.exit_code == 0
    assert "Automation started" in caplog.text
    assert "Login successful" in caplog.text
    assert "Download started" in caplog.text
    assert "File downloaded successfully: report.txt" in caplog.text
    assert "Automation completed successfully" in caplog.text


def test_successful_run_sends_success_notification(fake_playwright, monkeypatch, mock_notify):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "demo123")

    result = runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    assert result.exit_code == 0
    mock_notify.assert_called_once()
    message = mock_notify.call_args[0][0]
    assert "SUCCESS" in message
    assert "site=demo_portal" in message
    assert "file=report.txt" in message


def test_login_failure_returns_failure_and_notifies(fake_playwright, monkeypatch, mock_notify):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "wrong")
    page = fake_playwright.chromium.launch.return_value.new_page.return_value
    page.wait_for_url.side_effect = PlaywrightTimeoutError("Timeout 3000ms exceeded")

    result = runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    assert result.exit_code == 1
    page.expect_download.assert_not_called()  # never reached the download step
    mock_notify.assert_called_once()
    message = mock_notify.call_args[0][0]
    assert "FAILURE" in message
    assert "step=login" in message
    assert "attempts=3" in message
    assert "error=Timeout 3000ms exceeded" in message


def test_programming_bug_during_login_is_not_swallowed(fake_playwright, monkeypatch, mock_notify):
    """A real bug (not a Playwright timeout) must crash loudly, not be reported as a failed step."""
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "demo123")
    page = fake_playwright.chromium.launch.return_value.new_page.return_value
    page.wait_for_url.side_effect = AttributeError("'NoneType' object has no attribute 'foo'")

    result = runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    assert isinstance(result.exception, AttributeError)
    mock_notify.assert_not_called()


def test_download_failure_returns_failure_and_notifies(fake_playwright, monkeypatch, mock_notify):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "demo123")
    page = fake_playwright.chromium.launch.return_value.new_page.return_value
    page.expect_download.side_effect = PlaywrightTimeoutError("Timeout 3000ms exceeded")

    result = runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    assert result.exit_code == 1
    page.wait_for_url.assert_called_once()  # login step did succeed
    mock_notify.assert_called_once()
    message = mock_notify.call_args[0][0]
    assert "FAILURE" in message
    assert "step=download" in message
    assert "attempts=3" in message
    assert "error=Timeout 3000ms exceeded" in message


def test_failure_notification_never_contains_the_password(
    fake_playwright, monkeypatch, mock_notify
):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "s3cr3t-value")
    page = fake_playwright.chromium.launch.return_value.new_page.return_value
    page.wait_for_url.side_effect = PlaywrightTimeoutError("timeout")

    runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    message = mock_notify.call_args[0][0]
    assert "s3cr3t-value" not in message


def test_failure_logs_are_clear(fake_playwright, monkeypatch, caplog):
    monkeypatch.setenv("PORTAL_USERNAME", "demo")
    monkeypatch.setenv("PORTAL_PASSWORD", "wrong")
    page = fake_playwright.chromium.launch.return_value.new_page.return_value
    page.wait_for_url.side_effect = PlaywrightTimeoutError("Timeout 3000ms exceeded")

    with caplog.at_level(logging.INFO):
        runner.invoke(make_app(), ["--site", "demo_portal", "--no-display-browser"])

    assert "Login failed after 3 attempts: Timeout 3000ms exceeded" in caplog.text
    assert "Sending failure notification" in caplog.text
    assert "Automation failed" in caplog.text


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
