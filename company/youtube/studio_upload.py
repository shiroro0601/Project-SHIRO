from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from company.runtime.real_video_runtime import VideoOutputValidator


STATUS_LOGGED_IN = "logged_in"
STATUS_LOGIN_REQUIRED = "login_required"
STATUS_CHANNEL_UNAVAILABLE = "channel_unavailable"
STATUS_STUDIO_UNAVAILABLE = "studio_unavailable"
STATUS_TIMEOUT = "timeout"
STATUS_UNKNOWN = "unknown"


@dataclass(frozen=True)
class YouTubeBrowserConfig:
    user_data_dir: Path = Path("outputs/browser_profiles/youtube")
    headless: bool = False
    browser_channel: str | None = None
    executable_path: str | None = None
    timeout_ms: int = 30000
    slow_mo_ms: int = 0
    locale: str = "ja-JP"
    studio_url: str = "https://studio.youtube.com/"

    def __post_init__(self):
        object.__setattr__(self, "user_data_dir", Path(self.user_data_dir))


@dataclass(frozen=True)
class YouTubeCDPConfig:
    endpoint_url: str = "http://127.0.0.1:9222"
    timeout_ms: int = 30000
    studio_url: str = "https://studio.youtube.com/"

    def __post_init__(self):
        _validate_cdp_endpoint(self.endpoint_url)


def _validate_cdp_endpoint(endpoint_url: str) -> None:
    parsed = urlparse(endpoint_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("CDP endpoint must use http or https.")
    if hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("CDP endpoint must point to 127.0.0.1 or localhost.")


@dataclass(frozen=True)
class YouTubeStudioSelectors:
    create_button: tuple[str, ...] = (
        "ytcp-button#create-icon",
        "button[aria-label='Create']",
        "button[aria-label='作成']",
    )
    upload_videos_menu_item: tuple[str, ...] = (
        "tp-yt-paper-item#text-item-0",
        "tp-yt-paper-item:has-text('Upload videos')",
        "tp-yt-paper-item:has-text('動画をアップロード')",
    )
    file_input: tuple[str, ...] = ("input[type=file]",)
    file_select_button: tuple[str, ...] = (
        "text=ファイルを選択",
        "text=SELECT FILES",
        "button:has-text('ファイルを選択')",
        "button:has-text('SELECT FILES')",
        "ytcp-button:has-text('ファイルを選択')",
        "ytcp-button:has-text('SELECT FILES')",
    )
    dialog_file_input: tuple[str, ...] = (
        "ytcp-uploads-dialog input[type=file]",
        "tp-yt-paper-dialog input[type=file]",
        "input[type=file]",
    )
    details_dialog: tuple[str, ...] = (
        "ytcp-uploads-dialog",
        "ytcp-video-metadata-editor",
        "input[name=title]",
    )
    logged_in_indicators: tuple[str, ...] = (
        "ytcp-button#create-icon",
        "a[href*='/channel/']",
        "ytcp-app",
    )
    channel_unavailable_indicators: tuple[str, ...] = (
        "text=Create a channel",
        "text=チャンネルを作成",
    )
    save_button: tuple[str, ...] = ("button[data-test-id=draft-save]",)
    publish_button: tuple[str, ...] = ("button:has-text('Publish')",)
    next_button: tuple[str, ...] = ("ytcp-button:has-text('Next')",)


@dataclass
class YouTubeStudioLoginResult:
    status: str
    logged_in: bool
    current_url: str
    reason: str = ""


@dataclass
class UploadPreparationResult:
    status: str
    video_path: str
    filename: str
    upload_started: bool
    details_visible: bool
    logged_in: bool
    current_url: str
    published: bool = False
    saved: bool = False
    error: str = ""


class YouTubeStudioUploadError(Exception):
    pass


class PlaywrightCDPBrowserController:
    def __init__(
        self,
        config: YouTubeCDPConfig | None = None,
        sync_playwright_factory=None,
    ):
        self.config = config or YouTubeCDPConfig()
        self.sync_playwright_factory = sync_playwright_factory
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        try:
            factory = self.sync_playwright_factory or self._default_sync_playwright
            self.playwright = factory().start()
            self.browser = self.playwright.chromium.connect_over_cdp(
                self.config.endpoint_url,
                timeout=self.config.timeout_ms,
            )
            if not getattr(self.browser, "contexts", []):
                raise YouTubeStudioUploadError("cdp_context_unavailable")
            self.context = self.browser.contexts[0]
            self.page = (
                self.context.pages[0]
                if getattr(self.context, "pages", [])
                else self.context.new_page()
            )
            return self
        except YouTubeStudioUploadError:
            raise
        except Exception as exc:
            raise YouTubeStudioUploadError("cdp_connection_failed") from exc

    def close(self):
        # This controller attaches to a user-owned Chrome instance. Do not call
        # browser.close(), because that can close the user's real browser.
        if self.playwright is not None:
            self.playwright.stop()

    def open(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_ms)

    def click(self, selector: str) -> None:
        self.page.locator(selector).first.click(timeout=self.config.timeout_ms)

    def upload(self, selector: str, file_path: str) -> None:
        self.page.locator(selector).first.set_input_files(file_path)

    def choose_file(self, selectors: tuple[str, ...], file_path: str) -> bool:
        for selector in selectors:
            try:
                with self.page.expect_file_chooser(
                    timeout=self.config.timeout_ms
                ) as chooser_info:
                    self.page.locator(selector).first.click(
                        timeout=self.config.timeout_ms
                    )
                chooser_info.value.set_files(file_path)
                return True
            except Exception:
                continue
        return False

    def upload_in_frames(self, selectors: tuple[str, ...], file_path: str) -> bool:
        for frame in getattr(self.page, "frames", []) or []:
            for selector in selectors:
                try:
                    frame.locator(selector).first.set_input_files(file_path)
                    return True
                except Exception:
                    continue
        return False

    def wait_for_visible(self, selector: str) -> bool:
        try:
            self.page.locator(selector).first.wait_for(
                state="visible",
                timeout=self.config.timeout_ms,
            )
            return True
        except Exception:
            return False

    def is_visible(self, selector: str) -> bool:
        try:
            return bool(self.page.locator(selector).first.is_visible())
        except Exception:
            return False

    @property
    def current_url(self) -> str:
        return getattr(self.page, "url", "")

    def _default_sync_playwright(self):
        from playwright.sync_api import sync_playwright

        return sync_playwright()


class PlaywrightPersistentBrowserController:
    def __init__(
        self,
        config: YouTubeBrowserConfig,
        sync_playwright_factory=None,
    ):
        self.config = config
        self.sync_playwright_factory = sync_playwright_factory
        self.playwright = None
        self.context = None
        self.page = None

    def start(self):
        self.config.user_data_dir.mkdir(parents=True, exist_ok=True)
        try:
            factory = self.sync_playwright_factory or self._default_sync_playwright
            self.playwright = factory().start()
            kwargs = {
                "user_data_dir": str(self.config.user_data_dir),
                "headless": self.config.headless,
                "timeout": self.config.timeout_ms,
                "slow_mo": self.config.slow_mo_ms,
                "locale": self.config.locale,
            }
            if self.config.browser_channel:
                kwargs["channel"] = self.config.browser_channel
            if self.config.executable_path:
                kwargs["executable_path"] = self.config.executable_path
            self.context = self.playwright.chromium.launch_persistent_context(**kwargs)
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            return self
        except Exception as exc:
            raise YouTubeStudioUploadError("browser_launch_failed") from exc

    def close(self):
        if self.context is not None:
            self.context.close()
        if self.playwright is not None:
            self.playwright.stop()

    def open(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_ms)

    def click(self, selector: str) -> None:
        self.page.locator(selector).first.click(timeout=self.config.timeout_ms)

    def upload(self, selector: str, file_path: str) -> None:
        self.page.locator(selector).first.set_input_files(file_path)

    def choose_file(self, selectors: tuple[str, ...], file_path: str) -> bool:
        for selector in selectors:
            try:
                with self.page.expect_file_chooser(
                    timeout=self.config.timeout_ms
                ) as chooser_info:
                    self.page.locator(selector).first.click(
                        timeout=self.config.timeout_ms
                    )
                chooser_info.value.set_files(file_path)
                return True
            except Exception:
                continue
        return False

    def upload_in_frames(self, selectors: tuple[str, ...], file_path: str) -> bool:
        for frame in getattr(self.page, "frames", []) or []:
            for selector in selectors:
                try:
                    frame.locator(selector).first.set_input_files(file_path)
                    return True
                except Exception:
                    continue
        return False

    def wait_for_visible(self, selector: str) -> bool:
        try:
            self.page.locator(selector).first.wait_for(
                state="visible",
                timeout=self.config.timeout_ms,
            )
            return True
        except Exception:
            return False

    def is_visible(self, selector: str) -> bool:
        try:
            return bool(self.page.locator(selector).first.is_visible())
        except Exception:
            return False

    @property
    def current_url(self) -> str:
        return getattr(self.page, "url", "")

    def _default_sync_playwright(self):
        from playwright.sync_api import sync_playwright

        return sync_playwright()


class YouTubeStudioLoginChecker:
    def __init__(self, selectors: YouTubeStudioSelectors | None = None):
        self.selectors = selectors or YouTubeStudioSelectors()

    def check(self, browser) -> YouTubeStudioLoginResult:
        current_url = getattr(browser, "current_url", "")
        lowered_url = current_url.lower()
        if "accounts.google.com" in lowered_url or "signin" in lowered_url:
            return YouTubeStudioLoginResult(
                status=STATUS_LOGIN_REQUIRED,
                logged_in=False,
                current_url=current_url,
                reason="Google sign-in is required.",
            )
        if self._any_visible(browser, self.selectors.channel_unavailable_indicators):
            return YouTubeStudioLoginResult(
                status=STATUS_CHANNEL_UNAVAILABLE,
                logged_in=False,
                current_url=current_url,
                reason="YouTube channel is unavailable.",
            )
        if "studio.youtube.com" not in lowered_url:
            return YouTubeStudioLoginResult(
                status=STATUS_STUDIO_UNAVAILABLE,
                logged_in=False,
                current_url=current_url,
                reason="YouTube Studio is unavailable.",
            )
        if self._any_visible(browser, self.selectors.logged_in_indicators):
            return YouTubeStudioLoginResult(
                status=STATUS_LOGGED_IN,
                logged_in=True,
                current_url=current_url,
                reason="YouTube Studio UI is visible.",
            )
        return YouTubeStudioLoginResult(
            status=STATUS_UNKNOWN,
            logged_in=False,
            current_url=current_url,
            reason="Unable to determine login status.",
        )

    def _any_visible(self, browser, selectors: tuple[str, ...]) -> bool:
        return any(browser.is_visible(selector) for selector in selectors)


class YouTubeStudioUploadPreparer:
    def __init__(
        self,
        config: YouTubeBrowserConfig | None = None,
        browser=None,
        selectors: YouTubeStudioSelectors | None = None,
        login_checker: YouTubeStudioLoginChecker | None = None,
        validator: VideoOutputValidator | None = None,
    ):
        self.config = config or YouTubeBrowserConfig()
        self.browser = browser
        self.selectors = selectors or YouTubeStudioSelectors()
        self.login_checker = login_checker or YouTubeStudioLoginChecker(self.selectors)
        self.validator = validator or VideoOutputValidator()

    def login_only(self, keep_open: bool = False, input_func=input) -> YouTubeStudioLoginResult:
        browser, should_close = self._browser()
        try:
            browser.open(self.config.studio_url)
            result = self.login_checker.check(browser)
            if keep_open:
                input_func("Press Enter to close the browser...")
                result = self.login_checker.check(browser)
            return result
        finally:
            if should_close:
                browser.close()

    def prepare_upload(
        self,
        video_path: str,
        keep_open: bool = False,
        input_func=input,
    ) -> UploadPreparationResult:
        validation = self.validator.validate(video_path)
        absolute_path = str(Path(validation["video_path"]).resolve())
        browser, should_close = self._browser()
        try:
            browser.open(self.config.studio_url)
            login_result = self.login_checker.check(browser)
            if not login_result.logged_in:
                return UploadPreparationResult(
                    status=login_result.status,
                    video_path=absolute_path,
                    filename=Path(absolute_path).name,
                    upload_started=False,
                    details_visible=False,
                    logged_in=False,
                    current_url=login_result.current_url,
                    error=login_result.reason,
                )

            self._click_first_visible(browser, self.selectors.create_button, "create_button_not_found")
            self._click_first_visible(
                browser,
                self.selectors.upload_videos_menu_item,
                "upload_menu_not_found",
            )
            self._upload_first(browser, absolute_path)
            details_visible = self._wait_any_visible(browser, self.selectors.details_dialog)
            if not details_visible:
                raise YouTubeStudioUploadError("details_not_visible")
            if keep_open:
                input_func("Upload prepared. Press Enter to close the browser...")
            return UploadPreparationResult(
                status="prepared",
                video_path=absolute_path,
                filename=Path(absolute_path).name,
                upload_started=True,
                details_visible=True,
                logged_in=True,
                current_url=getattr(browser, "current_url", ""),
                published=False,
                saved=False,
                error="",
            )
        finally:
            if should_close:
                browser.close()

    def _browser(self):
        if self.browser is not None:
            return self.browser, False
        return PlaywrightPersistentBrowserController(self.config).start(), True

    def _click_first_visible(self, browser, selectors: tuple[str, ...], error: str) -> None:
        for selector in selectors:
            if browser.is_visible(selector):
                browser.click(selector)
                return
        raise YouTubeStudioUploadError(error)

    def _upload_first(self, browser, file_path: str) -> None:
        if hasattr(browser, "choose_file") and browser.choose_file(
            self.selectors.file_select_button,
            file_path,
        ):
            return
        for selector in self.selectors.file_input:
            try:
                browser.upload(selector, file_path)
                return
            except Exception:
                continue
        for selector in self.selectors.dialog_file_input:
            try:
                browser.upload(selector, file_path)
                return
            except Exception:
                continue
        if hasattr(browser, "upload_in_frames") and browser.upload_in_frames(
            self.selectors.file_input,
            file_path,
        ):
            return
        raise YouTubeStudioUploadError("file_input_not_found")

    def _wait_any_visible(self, browser, selectors: tuple[str, ...]) -> bool:
        return any(browser.wait_for_visible(selector) for selector in selectors)
