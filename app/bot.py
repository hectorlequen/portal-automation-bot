from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential

MAX_ATTEMPTS = 3


def _log_retry(step_name):
    def _before_sleep(retry_state):
        # retry_state.args holds the positional arguments the wrapped method was
        # called with. Since @retry decorates the plain function before it becomes
        # a bound method, args[0] is `self` — the PortalBot instance — which is how
        # this module-level callback reaches the instance's injected logger without
        # importing one itself.
        instance = retry_state.args[0]
        if instance.logger is not None:
            instance.logger.warning(
                "%s failed - retry %d/%d", step_name, retry_state.attempt_number, MAX_ATTEMPTS
            )

    return _before_sleep


class PortalBot:
    """Drives a Playwright page through a portal's login and report-download flow.

    Args:
        page: A Playwright ``Page`` already navigated to the login screen.
        username_selector: CSS selector for the username input.
        password_selector: CSS selector for the password input.
        login_button_selector: CSS selector for the login submit button.
        logger: Optional logger used to report retry attempts in
            ``check_login_success`` and ``download_report``. Nothing is logged
            if omitted.
    """

    def __init__(
        self, page, username_selector, password_selector, login_button_selector, logger=None
    ):
        self.page = page
        self.username_selector = username_selector
        self.password_selector = password_selector
        self.login_button_selector = login_button_selector
        self.logger = logger

    def login(self, username, password):
        """Fills in the login form and submits it.

        This does not wait for or verify that the login actually succeeded —
        call ``check_login_success`` afterwards to confirm it.
        """
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
        """Waits for the page to reach success_url_pattern after login.

        Retried up to MAX_ATTEMPTS times with exponential backoff whenever the
        page does not reach the expected URL in time.

        Args:
            success_url_pattern: Glob pattern the page URL must match on success.
            timeout: Max time in milliseconds to wait for the URL on each attempt.

        Raises:
            playwright.sync_api.TimeoutError: If the URL is never reached within
                timeout, after all MAX_ATTEMPTS attempts.
        """
        self.page.wait_for_url(success_url_pattern, timeout=timeout)

    @retry(
        stop=stop_after_attempt(MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        reraise=True,
        before_sleep=_log_retry("Download"),
    )
    def download_report(self, download_link_selector, destination_dir):
        """Clicks the download link and saves the resulting file to disk.

        Retried up to MAX_ATTEMPTS times with exponential backoff whenever the
        click does not trigger a completed download in time.

        Args:
            download_link_selector: CSS selector for the element that triggers
                the download.
            destination_dir: Directory the file is saved into; created if it
                does not already exist.

        Returns:
            Path of the saved file.

        Raises:
            playwright.sync_api.TimeoutError: If no download completes in time,
                after all MAX_ATTEMPTS attempts.
        """
        Path(destination_dir).mkdir(parents=True, exist_ok=True)
        with self.page.expect_download() as download_info:
            self.page.click(download_link_selector)
        download = download_info.value
        saved_path = Path(destination_dir) / download.suggested_filename
        download.save_as(saved_path)
        return saved_path
