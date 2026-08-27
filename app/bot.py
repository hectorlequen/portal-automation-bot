from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential


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

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=5), reraise=True
    )
    def download_report(self, download_link_selector, destination_dir):
        Path(destination_dir).mkdir(parents=True, exist_ok=True)
        with self.page.expect_download() as download_info:
            self.page.click(download_link_selector)
        download = download_info.value
        download.save_as(Path(destination_dir) / download.suggested_filename)
