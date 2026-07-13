from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeCDPConfig,
    YouTubeStudioPageResolver,
)


class FakeLocator:
    def __init__(self, visible=False):
        self.visible = visible

    @property
    def first(self):
        return self

    def is_visible(self):
        return self.visible

    def wait_for(self, state="visible", timeout=0):
        if not self.visible:
            raise RuntimeError("not visible")


class FakePage:
    def __init__(self, url="", visible_selectors=None, closed=False, active=False):
        self.url = url
        self.visible_selectors = set(visible_selectors or ())
        self.closed = closed
        self.active = active
        self.goto_calls = []
        self.close_called = False

    def is_closed(self):
        return self.closed

    def locator(self, selector):
        return FakeLocator(selector in self.visible_selectors)

    def evaluate(self, script):
        return self.active

    def goto(self, url, wait_until=None, timeout=0):
        self.url = url
        self.goto_calls.append(url)
        self.visible_selectors.add("ytcp-app")

    def close(self):
        self.close_called = True


class FakeContext:
    def __init__(self, pages=None):
        self.pages = list(pages or [])
        self.close_called = False

    def new_page(self):
        page = FakePage()
        self.pages.append(page)
        return page

    def close(self):
        self.close_called = True


class FakeBrowser:
    def __init__(self, contexts):
        self.contexts = contexts
        self.close_called = False

    def close(self):
        self.close_called = True


class FakeChromium:
    def __init__(self, browser):
        self.browser = browser
        self.endpoint = None

    def connect_over_cdp(self, endpoint_url, timeout=0):
        self.endpoint = endpoint_url
        return self.browser


class FakePlaywright:
    def __init__(self, browser):
        self.chromium = FakeChromium(browser)
        self.stop_called = False

    def stop(self):
        self.stop_called = True


class FakePlaywrightFactory:
    def __init__(self, browser):
        self.playwright = FakePlaywright(browser)

    def start(self):
        return self.playwright


def test_resolver_finds_studio_page_in_second_tab():
    other = FakePage("https://example.com/")
    studio = FakePage("https://studio.youtube.com/", {"ytcp-app"}, active=True)
    browser = FakeBrowser([FakeContext([other, studio])])

    result = YouTubeStudioPageResolver().resolve(browser)

    assert result.status == "resolved"
    assert result.page is studio
    assert result.reused_existing_page is True
    assert result.created_new_page is False
    assert result.candidate_count == 1


def test_resolver_searches_multiple_contexts_and_excludes_closed_page():
    closed_studio = FakePage("https://studio.youtube.com/", {"ytcp-app"}, closed=True)
    studio = FakePage("https://studio.youtube.com/", {"ytcp-app"})
    browser = FakeBrowser([FakeContext([closed_studio]), FakeContext([studio])])

    result = YouTubeStudioPageResolver().resolve(browser)

    assert result.page is studio
    assert result.candidate_count == 1


def test_resolver_creates_page_when_no_studio_candidate():
    context = FakeContext([FakePage("https://example.com/")])
    browser = FakeBrowser([context])

    result = YouTubeStudioPageResolver().resolve(browser)

    assert result.status == "resolved"
    assert result.reused_existing_page is False
    assert result.created_new_page is True
    assert result.page in context.pages
    assert result.page.goto_calls == ["https://studio.youtube.com/"]


def test_cdp_controller_uses_resolver_and_preserves_page_ownership():
    studio = FakePage("https://studio.youtube.com/", {"ytcp-app"})
    context = FakeContext([FakePage("https://example.com/"), studio])
    browser = FakeBrowser([context])
    factory = FakePlaywrightFactory(browser)

    controller = PlaywrightCDPBrowserController(
        config=YouTubeCDPConfig(endpoint_url="http://127.0.0.1:9222"),
        sync_playwright_factory=lambda: factory,
    ).start()

    assert controller.page is studio
    assert controller.context is context
    assert controller.owns_page is False
    controller.safe_disconnect()
    assert studio.close_called is False
    assert context.close_called is False
    assert browser.close_called is False


def test_cdp_controller_owns_only_new_page_when_created():
    context = FakeContext([])
    browser = FakeBrowser([context])
    factory = FakePlaywrightFactory(browser)

    controller = PlaywrightCDPBrowserController(
        config=YouTubeCDPConfig(endpoint_url="http://127.0.0.1:9222"),
        sync_playwright_factory=lambda: factory,
    ).start()

    assert controller.owns_page is True
    owned_page = controller.page
    controller.safe_disconnect()
    assert owned_page.close_called is True
    assert context.close_called is False
    assert browser.close_called is False
