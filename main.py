from pathlib import Path

from playwright.sync_api import TimeoutError, sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(Path("login_page.html").resolve().as_uri())
    page.fill("#username", "demo")
    page.fill("#password", "demo123")
    page.click("#login-btn")
    try:
        page.wait_for_url("**/dashboard.html", timeout=3000)
    except TimeoutError:
        print("Échec de connexion : identifiants probablement incorrects")

    print(page.url)
    page.wait_for_timeout(5000)
    browser.close()
