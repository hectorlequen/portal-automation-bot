import os

import requests

from app.logging_setup import logger


def notify_slack(message: str):
    """Posts message to the webhook URL configured via SLACK_WEBHOOK_URL.

    Never raises: does nothing if SLACK_WEBHOOK_URL is not set, and logs an
    error instead of raising if the HTTP request itself fails.

    Args:
        message: Text sent as-is as the notification body.
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.info("No Slack webhook URL found")
        return
    try:
        requests.post(webhook_url, json={"text": message})
    except requests.RequestException:
        logger.error("Failed to send Slack notification")


def format_success_message(site: str, filename: str) -> str:
    """Builds the notification body for a successful run.

    Returns:
        A "SUCCESS / site=... / file=..." message, one field per line.
    """
    return f"SUCCESS\nsite={site}\nfile={filename}"


def format_failure_message(site: str, step: str, error: str, attempts: int | None = None) -> str:
    """Builds the notification body for a failed run.

    Args:
        step: Name of the step that failed (e.g. "login", "download",
            "verification").
        error: Human-readable reason for the failure.
        attempts: Number of attempts made; the "attempts" line is omitted if
            None (e.g. for a step that doesn't retry, like verification).

    Returns:
        A "FAILURE / site=... / step=... / [attempts=...] / error=..." message,
        one field per line.
    """
    lines = ["FAILURE", f"site={site}", f"step={step}"]
    if attempts is not None:
        lines.append(f"attempts={attempts}")
    lines.append(f"error={error}")
    return "\n".join(lines)
