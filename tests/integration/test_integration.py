import threading
import time

import pytest
import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from app.bot import PortalBot
from app.config import config
from demo_portal.app import app as demo_portal_app

pytestmark = pytest.mark.integration

HOST = "127.0.0.1"
PORT = 5050
BASE_URL = f"http://{HOST}:{PORT}"


@pytest.fixture(scope="module")
def live_server():
    thread = threading.Thread(
        target=demo_portal_app.run,
        kwargs={"host": HOST, "port": PORT, "use_reloader": False},
        daemon=True,
    )
    thread.start()

    for _ in range(50):
        try:
            requests.get(BASE_URL, timeout=0.2)
            break
        except requests.ConnectionError:
            time.sleep(0.1)
    else:
        pytest.fail("demo_portal server did not start in time")

    yield BASE_URL


def test_full_login_and_download_flow(live_server, tmp_path):
    """Exercises config.yaml's real selectors against the real demo_portal HTML."""
    site_config = config["sites"]["demo_portal"]
    destination_dir = tmp_path / "downloads"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server}/login")

        bot = PortalBot(
            page,
            site_config["username_selector"],
            site_config["password_selector"],
            site_config["login_button_selector"],
        )
        bot.login("demo", "demo123")
        bot.check_login_success("**/dashboard")
        bot.download_report(site_config["download_link_selector"], str(destination_dir))

        browser.close()

    downloaded_files = list(destination_dir.iterdir())
    assert len(downloaded_files) == 1
    assert downloaded_files[0].read_text().startswith("invoice_id")


def test_login_with_wrong_credentials_never_reaches_dashboard(live_server):
    site_config = config["sites"]["demo_portal"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server}/login")

        bot = PortalBot(
            page,
            site_config["username_selector"],
            site_config["password_selector"],
            site_config["login_button_selector"],
        )
        bot.login("wrong", "wrong")

        with pytest.raises(PlaywrightTimeoutError):
            bot.check_login_success("**/dashboard", timeout=500)

        browser.close()
