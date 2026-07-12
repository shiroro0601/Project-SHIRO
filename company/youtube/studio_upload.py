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
    title_input: tuple[str, ...] = (
        "input[name=title]",
        "#title-textarea #textbox",
        "ytcp-social-suggestions-textbox#title-textarea #textbox",
        "ytcp-social-suggestions-textbox[aria-label*='Title']",
        "ytcp-social-suggestions-textbox[aria-label*='タイトル']",
        "[contenteditable=true][aria-label*='Title']",
        "[contenteditable=true][aria-label*='タイトル']",
    )
    description_input: tuple[str, ...] = (
        "textarea[name=description]",
        "#description-textarea #textbox",
        "ytcp-social-suggestions-textbox#description-textarea #textbox",
        "ytcp-social-suggestions-textbox[aria-label*='Description']",
        "ytcp-social-suggestions-textbox[aria-label*='説明']",
        "[contenteditable=true][aria-label*='Description']",
        "[contenteditable=true][aria-label*='説明']",
    )
    made_for_kids_yes: tuple[str, ...] = (
        "tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_MFK]",
        "ytcp-radio-button:has-text(\"Yes, it's made for kids\")",
        "ytcp-radio-button:has-text('はい、子ども向けです')",
        "text=Yes, it's made for kids",
        "text=はい、子ども向けです",
    )
    made_for_kids_no: tuple[str, ...] = (
        "tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]",
        "ytcp-radio-button:has-text(\"No, it's not made for kids\")",
        "ytcp-radio-button:has-text('いいえ、子ども向けではありません')",
        "text=No, it's not made for kids",
        "text=いいえ、子ども向けではありません",
    )
    show_more_button: tuple[str, ...] = (
        "ytcp-video-metadata-editor ytcp-button:has-text('すべて表示')",
        "ytcp-video-metadata-editor ytcp-button:has-text('SHOW MORE')",
        "ytcp-video-metadata-editor ytcp-button:has-text('もっと見る')",
        "ytcp-uploads-dialog ytcp-button:has-text('すべて表示')",
        "ytcp-uploads-dialog ytcp-button:has-text('SHOW MORE')",
        "ytcp-uploads-dialog ytcp-button:has-text('もっと見る')",
        "ytcp-button:has-text('もっと見る')",
        "ytcp-button:has-text('SHOW MORE')",
        "ytcp-button:has-text('すべて表示')",
        "button:has-text('もっと見る')",
        "button:has-text('SHOW MORE')",
        "button:has-text('すべて表示')",
        "text=もっと見る",
        "text=SHOW MORE",
        "text=すべて表示",
    )
    tags_input: tuple[str, ...] = (
        "input[aria-label='Tags']",
        "input[aria-label='タグ']",
        "#tags-container input",
        "ytcp-free-text-chip-bar input",
        "input#text-input",
        "ytcp-form-input-container:has-text('Tags') input",
        "ytcp-form-input-container:has-text('タグ') input",
        "input[name=tags]",
    )
    tag_chips: tuple[str, ...] = (
        "ytcp-chip-bar ytcp-chip",
        "ytcp-chip",
        "[id*=chip]",
    )


@dataclass(frozen=True)
class YouTubeVideoMetadata:
    title: str
    description: str
    made_for_kids: bool
    tags: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "title", str(self.title).strip())
        object.__setattr__(self, "description", str(self.description))
        object.__setattr__(self, "tags", self._normalize_tags(self.tags))

    def _normalize_tags(self, tags) -> tuple[str, ...]:
        seen = set()
        normalized = []
        for tag in tuple(tags or ()):
            clean = str(tag).strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            normalized.append(clean)
        return tuple(normalized)


@dataclass
class YouTubeMetadataPreparationResult:
    status: str
    video_path: str
    title: str
    description: str
    made_for_kids: bool
    tags: tuple[str, ...]
    title_applied: bool
    description_applied: bool
    audience_applied: bool
    tags_applied: bool
    saved: bool = False
    published: bool = False
    error: str = ""


class YouTubeMetadataValidationError(ValueError):
    pass


class YouTubeMetadataValidator:
    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_TAG_LENGTH = 100
    MAX_TAGS_TOTAL_LENGTH = 500

    def validate(self, metadata: YouTubeVideoMetadata) -> YouTubeVideoMetadata:
        if not isinstance(metadata.made_for_kids, bool):
            raise YouTubeMetadataValidationError("made_for_kids must be bool.")
        self._validate_title(metadata.title)
        self._validate_description(metadata.description)
        self._validate_tags(metadata.tags)
        return metadata

    def _validate_title(self, title: str) -> None:
        if not title:
            raise YouTubeMetadataValidationError("title is required.")
        if len(title) > self.MAX_TITLE_LENGTH:
            raise YouTubeMetadataValidationError("title must be 100 characters or less.")
        if "\n" in title or "\r" in title:
            raise YouTubeMetadataValidationError("title must not contain newlines.")
        if self._has_control_chars(title, allow_newlines=False):
            raise YouTubeMetadataValidationError("title contains control characters.")

    def _validate_description(self, description: str) -> None:
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            raise YouTubeMetadataValidationError(
                "description must be 5000 characters or less."
            )
        if self._has_control_chars(description, allow_newlines=True):
            raise YouTubeMetadataValidationError(
                "description contains control characters."
            )

    def _validate_tags(self, tags: tuple[str, ...]) -> None:
        total = 0
        for tag in tags:
            if "," in tag:
                raise YouTubeMetadataValidationError(
                    "tags must not contain commas; pass each tag separately."
                )
            if len(tag) > self.MAX_TAG_LENGTH:
                raise YouTubeMetadataValidationError("tag is too long.")
            if self._has_control_chars(tag, allow_newlines=False):
                raise YouTubeMetadataValidationError("tag contains control characters.")
            total += len(tag)
        if total > self.MAX_TAGS_TOTAL_LENGTH:
            raise YouTubeMetadataValidationError("tags total length is too long.")

    def _has_control_chars(self, value: str, allow_newlines: bool) -> bool:
        allowed = {"\n", "\r", "\t"} if allow_newlines else set()
        return any(ord(char) < 32 and char not in allowed for char in value)


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
        if "studio.youtube.com" in url and "studio.youtube.com" in self.current_url:
            return
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_ms)

    def click(self, selector: str) -> None:
        self.page.locator(selector).first.click(timeout=self.config.timeout_ms)

    def _first_existing(self, selector: str):
        locator = self.page.locator(selector)
        try:
            if locator.count() <= 0:
                return None
        except Exception:
            return None
        return locator.first

    def click_first(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            try:
                locator = self._first_existing(selector)
                if locator is None:
                    continue
                locator.click(timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

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

    def fill_text(self, selectors: tuple[str, ...], value: str) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.fill(value, timeout=self.config.timeout_ms)
                return True
            except Exception:
                try:
                    locator.click(timeout=self.config.timeout_ms)
                    locator.press("Control+A", timeout=self.config.timeout_ms)
                    locator.type(value, timeout=self.config.timeout_ms)
                    return True
                except Exception:
                    continue
        return False

    def read_text(self, selectors: tuple[str, ...]) -> str:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return locator.input_value(timeout=self.config.timeout_ms)
            except Exception:
                try:
                    return locator.text_content(timeout=self.config.timeout_ms) or ""
                except Exception:
                    try:
                        return (
                            locator.evaluate(
                                "el => el.value ?? el.innerText ?? el.textContent ?? ''"
                            )
                            or ""
                        )
                    except Exception:
                        continue
        return ""

    def is_checked(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return bool(locator.is_checked(timeout=self.config.timeout_ms))
            except Exception:
                try:
                    return locator.get_attribute("aria-checked") == "true"
                except Exception:
                    continue
        return False

    def add_tags(self, selectors: tuple[str, ...], tags: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.click(timeout=self.config.timeout_ms)
                locator.press("Control+A", timeout=self.config.timeout_ms)
                locator.press("Backspace", timeout=self.config.timeout_ms)
                for tag in tags:
                    locator.type(tag, timeout=self.config.timeout_ms)
                    locator.press("Enter", timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

    def read_tags(
        self,
        chip_selectors: tuple[str, ...],
        input_selectors: tuple[str, ...],
    ) -> tuple[str, ...]:
        for selector in chip_selectors:
            try:
                values = self.page.locator(selector).all_text_contents()
                clean = tuple(value.strip() for value in values if value.strip())
                if clean:
                    return clean
            except Exception:
                continue
        text = self.read_text(input_selectors)
        if not text:
            return ()
        return tuple(part.strip() for part in text.split(",") if part.strip())

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
        if "studio.youtube.com" in url and "studio.youtube.com" in self.current_url:
            return
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout_ms)

    def click(self, selector: str) -> None:
        self.page.locator(selector).first.click(timeout=self.config.timeout_ms)

    def _first_existing(self, selector: str):
        locator = self.page.locator(selector)
        try:
            if locator.count() <= 0:
                return None
        except Exception:
            return None
        return locator.first

    def click_first(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            try:
                locator = self._first_existing(selector)
                if locator is None:
                    continue
                locator.click(timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

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

    def fill_text(self, selectors: tuple[str, ...], value: str) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.fill(value, timeout=self.config.timeout_ms)
                return True
            except Exception:
                try:
                    locator.click(timeout=self.config.timeout_ms)
                    locator.press("Control+A", timeout=self.config.timeout_ms)
                    locator.type(value, timeout=self.config.timeout_ms)
                    return True
                except Exception:
                    continue
        return False

    def read_text(self, selectors: tuple[str, ...]) -> str:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return locator.input_value(timeout=self.config.timeout_ms)
            except Exception:
                try:
                    return locator.text_content(timeout=self.config.timeout_ms) or ""
                except Exception:
                    try:
                        return (
                            locator.evaluate(
                                "el => el.value ?? el.innerText ?? el.textContent ?? ''"
                            )
                            or ""
                        )
                    except Exception:
                        continue
        return ""

    def is_checked(self, selectors: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                return bool(locator.is_checked(timeout=self.config.timeout_ms))
            except Exception:
                try:
                    return locator.get_attribute("aria-checked") == "true"
                except Exception:
                    continue
        return False

    def add_tags(self, selectors: tuple[str, ...], tags: tuple[str, ...]) -> bool:
        for selector in selectors:
            locator = self._first_existing(selector)
            if locator is None:
                continue
            try:
                locator.click(timeout=self.config.timeout_ms)
                locator.press("Control+A", timeout=self.config.timeout_ms)
                locator.press("Backspace", timeout=self.config.timeout_ms)
                for tag in tags:
                    locator.type(tag, timeout=self.config.timeout_ms)
                    locator.press("Enter", timeout=self.config.timeout_ms)
                return True
            except Exception:
                continue
        return False

    def read_tags(
        self,
        chip_selectors: tuple[str, ...],
        input_selectors: tuple[str, ...],
    ) -> tuple[str, ...]:
        for selector in chip_selectors:
            try:
                values = self.page.locator(selector).all_text_contents()
                clean = tuple(value.strip() for value in values if value.strip())
                if clean:
                    return clean
            except Exception:
                continue
        text = self.read_text(input_selectors)
        if not text:
            return ()
        return tuple(part.strip() for part in text.split(",") if part.strip())

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


class YouTubeMetadataPreparer:
    def __init__(
        self,
        upload_preparer: YouTubeStudioUploadPreparer,
        selectors: YouTubeStudioSelectors | None = None,
        validator: YouTubeMetadataValidator | None = None,
    ):
        self.upload_preparer = upload_preparer
        self.selectors = selectors or upload_preparer.selectors
        self.validator = validator or YouTubeMetadataValidator()

    def prepare_metadata(
        self,
        video_path: str,
        metadata: YouTubeVideoMetadata,
        keep_open: bool = False,
        input_func=input,
    ) -> YouTubeMetadataPreparationResult:
        try:
            metadata = self.validator.validate(metadata)
        except YouTubeMetadataValidationError as exc:
            return self._failed(metadata, str(video_path), "invalid_metadata", str(exc))

        upload_result = self._prepare_or_reuse_upload(video_path)
        if upload_result.status != "prepared":
            return self._failed(
                metadata,
                upload_result.video_path,
                upload_result.status,
                upload_result.error,
            )

        browser = self.upload_preparer.browser
        try:
            title_applied = self._apply_text(
                browser,
                self.selectors.title_input,
                metadata.title,
                "title_input_not_found",
                "title_apply_failed",
            )
            description_applied = self._apply_text(
                browser,
                self.selectors.description_input,
                metadata.description,
                "description_input_not_found",
                "description_apply_failed",
            )
            audience_applied = self._apply_audience(browser, metadata.made_for_kids)
            tags_applied = self._apply_tags(browser, metadata.tags)
            if keep_open:
                input_func("Metadata prepared. Press Enter to close the browser...")
            return YouTubeMetadataPreparationResult(
                status="metadata_prepared",
                video_path=upload_result.video_path,
                title=metadata.title,
                description=metadata.description,
                made_for_kids=metadata.made_for_kids,
                tags=metadata.tags,
                title_applied=title_applied,
                description_applied=description_applied,
                audience_applied=audience_applied,
                tags_applied=tags_applied,
                saved=False,
                published=False,
                error="",
            )
        except YouTubeStudioUploadError as exc:
            return self._failed(metadata, upload_result.video_path, str(exc), str(exc))

    def _apply_text(
        self,
        browser,
        selectors: tuple[str, ...],
        value: str,
        not_found_error: str,
        apply_error: str,
    ) -> bool:
        if not browser.fill_text(selectors, value):
            raise YouTubeStudioUploadError(not_found_error)
        actual = browser.read_text(selectors)
        if not self._text_matches(actual, value):
            raise YouTubeStudioUploadError(apply_error)
        return True

    def _text_matches(self, actual: str, expected: str) -> bool:
        return actual == expected or actual.rstrip("\n") == expected

    def _apply_audience(self, browser, made_for_kids: bool) -> bool:
        target = (
            self.selectors.made_for_kids_yes
            if made_for_kids
            else self.selectors.made_for_kids_no
        )
        other = (
            self.selectors.made_for_kids_no
            if made_for_kids
            else self.selectors.made_for_kids_yes
        )
        if not browser.click_first(target):
            raise YouTubeStudioUploadError("audience_control_not_found")
        if not browser.is_checked(target) or browser.is_checked(other):
            raise YouTubeStudioUploadError("audience_apply_failed")
        return True

    def _apply_tags(self, browser, tags: tuple[str, ...]) -> bool:
        if tags and not self._ensure_tags_visible(browser):
            raise YouTubeStudioUploadError("show_more_not_found")
        if not browser.add_tags(self.selectors.tags_input, tags):
            raise YouTubeStudioUploadError("tags_input_not_found")
        actual = browser.read_tags(self.selectors.tag_chips, self.selectors.tags_input)
        if tuple(actual) != tuple(tags):
            raise YouTubeStudioUploadError("tags_apply_failed")
        return True

    def _prepare_or_reuse_upload(self, video_path: str) -> UploadPreparationResult:
        browser = self.upload_preparer.browser
        if browser is not None and self._details_visible(browser):
            validation = self.upload_preparer.validator.validate(video_path)
            absolute_path = str(Path(validation["video_path"]).resolve())
            return UploadPreparationResult(
                status="prepared",
                video_path=absolute_path,
                filename=Path(absolute_path).name,
                upload_started=True,
                details_visible=True,
                logged_in=True,
                current_url=getattr(browser, "current_url", ""),
                saved=False,
                published=False,
                error="",
            )
        return self.upload_preparer.prepare_upload(video_path, keep_open=False)

    def _details_visible(self, browser) -> bool:
        return any(browser.is_visible(selector) for selector in self.selectors.details_dialog)

    def _ensure_tags_visible(self, browser) -> bool:
        if any(browser.is_visible(selector) for selector in self.selectors.tags_input):
            return True
        if browser.click_first(self.selectors.show_more_button):
            return True
        return any(browser.is_visible(selector) for selector in self.selectors.tags_input)

    def _failed(
        self,
        metadata: YouTubeVideoMetadata,
        video_path: str,
        status: str,
        error: str,
    ) -> YouTubeMetadataPreparationResult:
        return YouTubeMetadataPreparationResult(
            status=status,
            video_path=str(video_path),
            title=getattr(metadata, "title", ""),
            description=getattr(metadata, "description", ""),
            made_for_kids=bool(getattr(metadata, "made_for_kids", False)),
            tags=tuple(getattr(metadata, "tags", ()) or ()),
            title_applied=False,
            description_applied=False,
            audience_applied=False,
            tags_applied=False,
            saved=False,
            published=False,
            error=error,
        )
