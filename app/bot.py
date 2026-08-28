from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential

from app.logging_setup import logger

MAX_ATTEMPTS = 3


def _log_retry(step_name):
    def _before_sleep(retry_state):
        logger.warning(
            "%s failed - retry %d/%d", step_name, retry_state.attempt_number, MAX_ATTEMPTS
        )

    return _before_sleep


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
        stop=stop_after_attempt(MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        reraise=True,
        before_sleep=_log_retry("Login"),
    )
    def check_login_success(self, success_url_pattern, timeout=3000):
        self.page.wait_for_url(success_url_pattern, timeout=timeout)

    @retry(
        stop=stop_after_attempt(MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        reraise=True,
        before_sleep=_log_retry("Download"),
    )
    def download_report(self, download_link_selector, destination_dir):
        Path(destination_dir).mkdir(parents=True, exist_ok=True)
        with self.page.expect_download() as download_info:
            self.page.click(download_link_selector)
        download = download_info.value
        saved_path = Path(destination_dir) / download.suggested_filename
        download.save_as(saved_path)
        return saved_path
