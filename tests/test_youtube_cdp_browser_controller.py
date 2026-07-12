import pytest

from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeCDPConfig,
    YouTubeStudioUploadError,
)


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


class FakeFileChooser:
    def __init__(self, page):
        self.page = page

    def set_files(self, file_path):
        self.page.actions.append(("chooser.set_files", file_path))


class FakeFileChooserContext:
    def __init__(self, page, timeout=None):
        self.page = page
        self.timeout = timeout
        self.value = FakeFileChooser(page)

    def __enter__(self):
        self.page.actions.append(("expect_file_chooser", self.timeout))
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePage:
    def __init__(self):
        self.actions = []
        self.url = "https://studio.youtube.com/"
        self.visible_selectors = {"ytcp-app"}

    def goto(self, url, wait_until=None, timeout=None):
        self.url = url
        self.actions.append(("goto", url, wait_until, timeout))

    def locator(self, selector):
        return FakeLocatorFirst(self, selector)

    def expect_file_chooser(self, timeout=None):
        return FakeFileChooserContext(self, timeout=timeout)


class FakeContext:
    def __init__(self, pages=None):
        self.pages = list(pages or [])
        self.new_page_called = False

    def new_page(self):
        self.new_page_called = True
        page = FakePage()
        self.pages.append(page)
        return page


class FakeBrowser:
    def __init__(self, contexts):
        self.contexts = contexts
        self.closed = False

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self, browser):
        self.browser = browser
        self.endpoint_url = None
        self.timeout = None

    def connect_over_cdp(self, endpoint_url, timeout=None):
        self.endpoint_url = endpoint_url
        self.timeout = timeout
        return self.browser


class FakePlaywright:
    def __init__(self, browser):
        self.chromium = FakeChromium(browser)
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeSyncPlaywright:
    def __init__(self, playwright):
        self.playwright = playwright

    def start(self):
        return self.playwright


def test_cdp_config_allows_localhost_and_127():
    assert YouTubeCDPConfig(endpoint_url="http://127.0.0.1:9222").endpoint_url
    assert YouTubeCDPConfig(endpoint_url="http://localhost:9222").endpoint_url


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://0.0.0.0:9222",
        "http://192.168.0.10:9222",
        "http://example.com:9222",
    ],
)
def test_cdp_config_rejects_external_hosts(endpoint):
    with pytest.raises(ValueError):
        YouTubeCDPConfig(endpoint_url=endpoint)


def test_cdp_controller_connects_over_cdp_with_endpoint():
    page = FakePage()
    context = FakeContext(pages=[page])
    browser = FakeBrowser(contexts=[context])
    playwright = FakePlaywright(browser)
    config = YouTubeCDPConfig(
        endpoint_url="http://127.0.0.1:9222",
        timeout_ms=12345,
    )

    controller = PlaywrightCDPBrowserController(
        config=config,
        sync_playwright_factory=lambda: FakeSyncPlaywright(playwright),
    ).start()

    assert playwright.chromium.endpoint_url == "http://127.0.0.1:9222"
    assert playwright.chromium.timeout == 12345
    assert controller.context is context
    assert controller.page is page
    assert context.new_page_called is False


def test_cdp_controller_uses_new_page_when_context_has_no_pages():
    context = FakeContext(pages=[])
    browser = FakeBrowser(contexts=[context])
    playwright = FakePlaywright(browser)

    controller = PlaywrightCDPBrowserController(
        sync_playwright_factory=lambda: FakeSyncPlaywright(playwright),
    ).start()

    assert context.new_page_called is True
    assert controller.page is context.pages[0]


def test_cdp_controller_does_not_close_user_chrome():
    context = FakeContext(pages=[FakePage()])
    browser = FakeBrowser(contexts=[context])
    playwright = FakePlaywright(browser)
    controller = PlaywrightCDPBrowserController(
        sync_playwright_factory=lambda: FakeSyncPlaywright(playwright),
    ).start()

    controller.close()

    assert browser.closed is False
    assert playwright.stopped is True


def test_cdp_controller_delegates_page_operations_without_save_or_publish():
    page = FakePage()
    context = FakeContext(pages=[page])
    browser = FakeBrowser(contexts=[context])
    playwright = FakePlaywright(browser)
    controller = PlaywrightCDPBrowserController(
        sync_playwright_factory=lambda: FakeSyncPlaywright(playwright),
    ).start()

    controller.open("https://studio.youtube.com/")
    controller.click("ytcp-button#create-icon")
    controller.upload("input[type=file]", "video.mp4")
    controller.wait_for_visible("ytcp-uploads-dialog")

    assert page.actions == [
        ("goto", "https://studio.youtube.com/", "domcontentloaded", 30000),
        ("click", "ytcp-button#create-icon", 30000),
        ("set_input_files", "input[type=file]", "video.mp4"),
        ("wait_for", "ytcp-uploads-dialog", "visible", 30000),
    ]
    assert not any("draft-save" in str(action) for action in page.actions)
    assert not any("Publish" in str(action) for action in page.actions)


def test_cdp_controller_uses_expect_file_chooser_before_set_files():
    page = FakePage()
    context = FakeContext(pages=[page])
    browser = FakeBrowser(contexts=[context])
    playwright = FakePlaywright(browser)
    controller = PlaywrightCDPBrowserController(
        sync_playwright_factory=lambda: FakeSyncPlaywright(playwright),
    ).start()

    handled = controller.choose_file(("text=ファイルを選択",), "video.mp4")

    assert handled is True
    assert page.actions == [
        ("expect_file_chooser", 30000),
        ("click", "text=ファイルを選択", 30000),
        ("chooser.set_files", "video.mp4"),
    ]


def test_cdp_controller_can_upload_input_inside_frame():
    class FakeFrame:
        def __init__(self):
            self.actions = []

        def locator(self, selector):
            return FakeLocatorFirst(self, selector)

    page = FakePage()
    frame = FakeFrame()
    page.frames = [frame]
    context = FakeContext(pages=[page])
    browser = FakeBrowser(contexts=[context])
    playwright = FakePlaywright(browser)
    controller = PlaywrightCDPBrowserController(
        sync_playwright_factory=lambda: FakeSyncPlaywright(playwright),
    ).start()

    handled = controller.upload_in_frames(("input[type=file]",), "video.mp4")

    assert handled is True
    assert frame.actions == [("set_input_files", "input[type=file]", "video.mp4")]


def test_cdp_controller_requires_existing_browser_context():
    browser = FakeBrowser(contexts=[])
    playwright = FakePlaywright(browser)
    controller = PlaywrightCDPBrowserController(
        sync_playwright_factory=lambda: FakeSyncPlaywright(playwright),
    )

    with pytest.raises(YouTubeStudioUploadError) as excinfo:
        controller.start()

    assert "cdp_context_unavailable" in str(excinfo.value)
