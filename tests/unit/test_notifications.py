from unittest.mock import MagicMock

import requests

from app.notifications import notify_slack


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
