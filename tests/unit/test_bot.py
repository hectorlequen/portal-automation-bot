import logging
from unittest.mock import MagicMock

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.bot import PortalBot


@pytest.fixture
def page():
    return MagicMock()


@pytest.fixture
def bot(page):
    return PortalBot(page, "#username", "#password", "button[type=submit]")


def test_login_fills_and_clicks_with_correct_selectors(bot, page):
    bot.login("demo", "demo123")
    page.fill.assert_any_call("#username", "demo")
    page.fill.assert_any_call("#password", "demo123")
    page.click.assert_called_once_with("button[type=submit]")


def test_check_login_success_waits_for_expected_url(bot, page):
    bot.check_login_success("**/dashboard", timeout=1234)
    page.wait_for_url.assert_called_once_with("**/dashboard", timeout=1234)


def test_check_login_success_retries_then_succeeds(bot, page, caplog):
    page.wait_for_url.side_effect = [
        PlaywrightTimeoutError("timeout"),
        PlaywrightTimeoutError("timeout"),
        None,
    ]
    with caplog.at_level(logging.WARNING):
        bot.check_login_success("**/dashboard")
    assert page.wait_for_url.call_count == 3
    assert "Login failed - retry 1/3" in caplog.text
    assert "Login failed - retry 2/3" in caplog.text


def test_check_login_success_reraises_after_max_attempts(bot, page):
    page.wait_for_url.side_effect = PlaywrightTimeoutError("timeout")
    with pytest.raises(PlaywrightTimeoutError):
        bot.check_login_success("**/dashboard")
    assert page.wait_for_url.call_count == 3


def test_download_report_creates_destination_dir(bot, page, tmp_path):
    destination = tmp_path / "downloads"
    fake_download = MagicMock()
    fake_download.suggested_filename = "report.txt"
    page.expect_download.return_value.__enter__.return_value.value = fake_download

    bot.download_report('a[href="/download"]', str(destination))

    assert destination.is_dir()


def test_download_report_clicks_link_and_saves_file(bot, page, tmp_path):
    destination = tmp_path / "downloads"
    fake_download = MagicMock()
    fake_download.suggested_filename = "report.txt"
    page.expect_download.return_value.__enter__.return_value.value = fake_download

    saved_path = bot.download_report('a[href="/download"]', str(destination))

    page.click.assert_called_once_with('a[href="/download"]')
    fake_download.save_as.assert_called_once_with(destination / "report.txt")
    assert saved_path == destination / "report.txt"


def test_download_report_retries_on_failure(bot, page, tmp_path, caplog):
    fake_download = MagicMock()
    fake_download.suggested_filename = "report.txt"
    fake_context = MagicMock()
    fake_context.__enter__.return_value.value = fake_download
    page.expect_download.side_effect = [
        PlaywrightTimeoutError("timeout"),
        PlaywrightTimeoutError("timeout"),
        fake_context,
    ]

    with caplog.at_level(logging.WARNING):
        bot.download_report('a[href="/download"]', str(tmp_path / "downloads"))

    assert page.expect_download.call_count == 3
    assert "Download failed - retry 1/3" in caplog.text
    assert "Download failed - retry 2/3" in caplog.text


def test_download_report_reraises_after_max_attempts(bot, page, tmp_path):
    page.expect_download.side_effect = PlaywrightTimeoutError("timeout")
    with pytest.raises(PlaywrightTimeoutError):
        bot.download_report('a[href="/download"]', str(tmp_path / "downloads"))
    assert page.expect_download.call_count == 3
