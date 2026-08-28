import os

import requests

from app.logging_setup import logger


def notify_slack(message: str):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.info("No Slack webhook URL found")
        return
    try:
        requests.post(webhook_url, json={"text": message})
    except requests.RequestException:
        logger.error("Failed to send Slack notification")


def format_success_message(site: str, filename: str) -> str:
    return f"SUCCESS\nsite={site}\nfile={filename}"


def format_failure_message(site: str, step: str, error: str, attempts: int | None = None) -> str:
    lines = ["FAILURE", f"site={site}", f"step={step}"]
    if attempts is not None:
        lines.append(f"attempts={attempts}")
    lines.append(f"error={error}")
    return "\n".join(lines)
