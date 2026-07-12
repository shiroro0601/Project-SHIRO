from company.youtube.studio_upload import (
    PlaywrightPersistentBrowserController,
    YouTubeBrowserConfig,
    YouTubeStudioUploadError,
)
import pytest


class FakeLocatorFirst:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector
        self.first = self

    def click(self, timeout=None):
        self.page.actions.append(("click", self.selector, timeout))

    def set_input_files(self, file_path):
        self.page.actions.append(("set_input_files", self.selector, file_path))

    def wait_for(self, state=None, timeout=None):
        self.page.actions.append(("wait_for", self.selector, state, timeout))

    def is_visible(self):
        return self.selector in self.page.visible_selectors


class FakePage:
    def __init__(self):
        self.actions = []
        self.url = ""
        self.visible_selectors = set()

    def goto(self, url, wait_until=None, timeout=None):
        self.url = url
        self.actions.append(("goto", url, wait_until, timeout))

    def locator(self, selector):
        return FakeLocatorFirst(self, selector)


class FakeContext:
    def __init__(self):
        self.pages = [FakePage()]
        self.closed = False

    def new_page(self):
        page = FakePage()
        self.pages.append(page)
        return page

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self, context):
        self.context = context
        self.launch_kwargs = None

    def launch_persistent_context(self, **kwargs):
        self.launch_kwargs = kwargs
        return self.context


class FakePlaywright:
    def __init__(self, context):
        self.chromium = FakeChromium(context)
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeSyncPlaywright:
    def __init__(self, playwright):
        self.playwright = playwright

    def start(self):
        return self.playwright


def test_persistent_controller_uses_launch_persistent_context(tmp_path):
    context = FakeContext()
    playwright = FakePlaywright(context)
    config = YouTubeBrowserConfig(
        user_data_dir=tmp_path / "profile",
        headless=True,
        browser_channel="chrome",
        timeout_ms=40000,
        slow_mo_ms=10,
        locale="ja-JP",
    )

    controller = PlaywrightPersistentBrowserController(
        config=config,
        sync_playwright_factory=lambda: FakeSyncPlaywright(playwright),
    ).start()

    assert config.user_data_dir.exists()
    assert playwright.chromium.launch_kwargs["user_data_dir"] == str(config.user_data_dir)
    assert playwright.chromium.launch_kwargs["headless"] is True
    assert playwright.chromium.launch_kwargs["channel"] == "chrome"
    assert playwright.chromium.launch_kwargs["timeout"] == 40000
    assert playwright.chromium.launch_kwargs["slow_mo"] == 10
    assert playwright.chromium.launch_kwargs["locale"] == "ja-JP"
    assert controller.page is context.pages[0]


def test_persistent_controller_delegates_page_operations(tmp_path):
    context = FakeContext()
    playwright = FakePlaywright(context)
    controller = PlaywrightPersistentBrowserController(
        config=YouTubeBrowserConfig(user_data_dir=tmp_path / "profile"),
        sync_playwright_factory=lambda: FakeSyncPlaywright(playwright),
    ).start()

    controller.open("https://studio.youtube.com/")
    controller.click("button")
    controller.upload("input[type=file]", "video.mp4")
    controller.wait_for_visible("dialog")

    assert context.pages[0].actions == [
        ("goto", "https://studio.youtube.com/", "domcontentloaded", 30000),
        ("click", "button", 30000),
        ("set_input_files", "input[type=file]", "video.mp4"),
        ("wait_for", "dialog", "visible", 30000),
    ]

    controller.close()
    assert context.closed is True
    assert playwright.stopped is True


def test_persistent_controller_wraps_launch_failure(tmp_path):
    def failing_factory():
        raise RuntimeError("playwright missing")

    controller = PlaywrightPersistentBrowserController(
        config=YouTubeBrowserConfig(user_data_dir=tmp_path / "profile"),
        sync_playwright_factory=failing_factory,
    )

    with pytest.raises(YouTubeStudioUploadError) as excinfo:
        controller.start()

    assert "browser_launch_failed" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None
