import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from playwright.sync_api import TimeoutError, sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log")],
)
logger = logging.getLogger(__name__)

load_dotenv()

with open("config.yaml") as f:
    config = yaml.safe_load(f)
site_config = config["sites"]["demo_portal"]


class PortalBot:
    def __init__(self, page, username_selector, password_selector, login_button_selector):
        self.page = page
        self.username_selector = username_selector
        self.password_selector = password_selector
        self.login_button_selector = login_button_selector

    def login(self, username, password):
        self.page.fill(self.username_selector, username)
        self.page.fill(self.password_selector, password)
        self.page.click(self.login_button_selector)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=5), reraise=True
    )
    def check_login_success(self, success_url_pattern, timeout=3000):
        self.page.wait_for_url(success_url_pattern, timeout=timeout)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(Path(site_config["url_login"]).resolve().as_uri())

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
    except TimeoutError:
        logger.error("Login failed: credentials are probably incorrect")

    logger.info(page.url)
    page.wait_for_timeout(5000)
    browser.close()
