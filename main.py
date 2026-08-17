from pathlib import Path

from playwright.sync_api import TimeoutError, sync_playwright


def login(
    page,
    username_selector,
    password_selector,
    login_button_selector,
    username,
    password,
):
    page.fill(username_selector, username)
    page.fill(password_selector, password)
    page.click(login_button_selector)


def check_login_success(page, success_url_pattern, timeout=3000):
    page.wait_for_url(success_url_pattern, timeout=timeout)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(Path("login_page.html").resolve().as_uri())
    login(page, "#username", "#password", "#login-btn", "demo", "demo123")
    try:
        check_login_success(page, "**/dashboard.html")
    except TimeoutError:
        print("Login failed: credentials are probably incorrect")

    print(page.url)
    page.wait_for_timeout(5000)
    browser.close()
