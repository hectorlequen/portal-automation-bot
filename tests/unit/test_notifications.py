from unittest.mock import MagicMock

import requests

from app.notifications import format_failure_message, format_success_message, notify_slack


def test_notify_slack_without_webhook_url_does_not_post(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    mock_post = MagicMock()
    monkeypatch.setattr(requests, "post", mock_post)

    notify_slack("hello")

    mock_post.assert_not_called()


def test_notify_slack_with_webhook_url_posts_message(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://example.test/webhook")
    mock_post = MagicMock()
    monkeypatch.setattr(requests, "post", mock_post)

    notify_slack("hello")

    mock_post.assert_called_once_with("https://example.test/webhook", json={"text": "hello"})


def test_notify_slack_swallows_request_exception(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://example.test/webhook")
    mock_post = MagicMock(side_effect=requests.RequestException("network error"))
    monkeypatch.setattr(requests, "post", mock_post)

    notify_slack("hello")  # must not raise


def test_format_success_message_contains_required_fields():
    message = format_success_message("demo_portal", "report.txt")
    assert "SUCCESS" in message
    assert "site=demo_portal" in message
    assert "file=report.txt" in message


def test_format_failure_message_contains_required_fields():
    message = format_failure_message("demo_portal", "login", "Timeout 3000ms exceeded", attempts=3)
    assert "FAILURE" in message
    assert "site=demo_portal" in message
    assert "step=login" in message
    assert "attempts=3" in message
    assert "error=Timeout 3000ms exceeded" in message


def test_format_failure_message_omits_attempts_when_not_given():
    message = format_failure_message("demo_portal", "verification", "file not found on disk")
    assert "attempts=" not in message
