from pathlib import Path

from playwright.sync_api import TimeoutError, sync_playwright


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

    def check_login_success(self, success_url_pattern, timeout=3000):
        self.page.wait_for_url(success_url_pattern, timeout=timeout)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(Path("login_page.html").resolve().as_uri())

    bot = PortalBot(page, "#username", "#password", "#login-btn")
    bot.login("demo", "demo123")
    try:
        bot.check_login_success("**/dashboard.html")
    except TimeoutError:
        print("Login failed: credentials are probably incorrect")

    print(page.url)
    page.wait_for_timeout(5000)
    browser.close()
