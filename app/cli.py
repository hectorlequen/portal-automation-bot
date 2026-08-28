import os

import typer
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from app.bot import MAX_ATTEMPTS, PortalBot
from app.config import BASE_DIR, get_site_config
from app.logging_setup import logger
from app.notifications import format_failure_message, format_success_message, notify_slack

DOWNLOAD_DIR = BASE_DIR / "downloads"


def main(
    site: str = typer.Option("demo_portal", help="Site name from config.yaml"),
    display_browser: bool = typer.Option(
        True, help="Show the browser window (use --no-display-browser to run headless)"
    ),
):
    logger.info("Automation started")
    site_config = get_site_config(site)

    portal_username = os.environ.get("PORTAL_USERNAME")
    portal_password = os.environ.get("PORTAL_PASSWORD")
    if not portal_username:
        raise EnvironmentError("PORTAL_USERNAME is missing from .env")
    if not portal_password:
        raise EnvironmentError("PORTAL_PASSWORD is missing from .env")

    failed_step = None
    failed_error = None
    saved_path = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not display_browser)
        page = browser.new_page()
        page.goto(site_config["url_login"])

        bot = PortalBot(
            page,
            site_config["username_selector"],
            site_config["password_selector"],
            site_config["login_button_selector"],
            logger=logger,
        )
        bot.login(portal_username, portal_password)

        try:
            bot.check_login_success(site_config["url_success"])
            logger.info("Login successful")
        except PlaywrightTimeoutError as exc:
            logger.error("Login failed after %d attempts: %s", MAX_ATTEMPTS, exc)
            failed_step = "login"
            failed_error = str(exc)

        if not failed_step:
            logger.info("Download started")
            try:
                saved_path = bot.download_report(
                    site_config["download_link_selector"], str(DOWNLOAD_DIR)
                )
            except PlaywrightTimeoutError as exc:
                logger.error("Download failed after %d attempts: %s", MAX_ATTEMPTS, exc)
                failed_step = "download"
                failed_error = str(exc)

        if not failed_step and not saved_path.exists():
            logger.error("Verification failed: downloaded file not found")
            failed_step = "verification"
            failed_error = "downloaded file not found on disk"

        page.wait_for_timeout(5000)
        browser.close()

    if failed_step:
        attempts = MAX_ATTEMPTS if failed_step in ("login", "download") else None
        logger.info("Sending failure notification")
        notify_slack(format_failure_message(site, failed_step, failed_error, attempts))
        logger.error("Automation failed")
        raise typer.Exit(code=1)

    logger.info("File downloaded successfully: %s", saved_path.name)
    notify_slack(format_success_message(site, saved_path.name))
    logger.info("Automation completed successfully")


if __name__ == "__main__":
    typer.run(main)
