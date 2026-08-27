import os

import typer
from playwright.sync_api import TimeoutError, sync_playwright

from app.bot import PortalBot
from app.config import BASE_DIR, get_site_config
from app.logging_setup import logger
from app.notifications import notify_slack

DOWNLOAD_DIR = BASE_DIR / "downloads"


def main(
    site: str = typer.Option("demo_portal", help="Site name from config.yaml"),
    display_browser: bool = typer.Option(
        True, help="Show the browser window (use --no-display-browser to run headless)"
    ),
):
    site_config = get_site_config(site)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not display_browser)
        page = browser.new_page()
        page.goto(site_config["url_login"])

        portal_username = os.environ.get("PORTAL_USERNAME")
        portal_password = os.environ.get("PORTAL_PASSWORD")
        if not portal_username:
            raise EnvironmentError("PORTAL_USERNAME is missing from .env")
        if not portal_password:
            raise EnvironmentError("PORTAL_PASSWORD is missing from .env")

        bot = PortalBot(
            page,
            site_config["username_selector"],
            site_config["password_selector"],
            site_config["login_button_selector"],
        )
        bot.login(portal_username, portal_password)
        try:
            bot.check_login_success(site_config["url_success"])
            bot.download_report(site_config["download_link_selector"], str(DOWNLOAD_DIR))
        except TimeoutError:
            logger.error("Login failed: credentials are probably incorrect")
            notify_slack(f"Login failed for site '{site}': credentials are probably incorrect")

        logger.info(page.url)
        page.wait_for_timeout(5000)
        browser.close()


if __name__ == "__main__":
    typer.run(main)
