from company.automation.browser import BrowserController
from company.automation.playwright_browser import PlaywrightBrowserController


class FakePage:
    def __init__(self):
        self.actions = []

    def goto(self, url: str) -> None:
        self.actions.append(("goto", url))

    def fill(self, selector: str, value: str) -> None:
        self.actions.append(("fill", selector, value))

    def click(self, selector: str) -> None:
        self.actions.append(("click", selector))

    def set_input_files(self, selector: str, file_path: str) -> None:
        self.actions.append(("set_input_files", selector, file_path))


def test_playwright_browser_controller_can_be_used_as_browser_controller():
    page = FakePage()
    browser: BrowserController = PlaywrightBrowserController(page=page)

    browser.open("https://studio.youtube.com")

    assert page.actions == [("goto", "https://studio.youtube.com")]


def test_playwright_browser_open_calls_page_goto():
    page = FakePage()
    browser = PlaywrightBrowserController(page=page)

    browser.open("https://studio.youtube.com")

    assert page.actions == [("goto", "https://studio.youtube.com")]


def test_playwright_browser_fill_calls_page_fill():
    page = FakePage()
    browser = PlaywrightBrowserController(page=page)

    browser.fill("input[name=title]", "猫の意外な雑学")

    assert page.actions == [
        ("fill", "input[name=title]", "猫の意外な雑学"),
    ]


def test_playwright_browser_click_calls_page_click():
    page = FakePage()
    browser = PlaywrightBrowserController(page=page)

    browser.click("button[data-test-id=draft-save]")

    assert page.actions == [("click", "button[data-test-id=draft-save]")]


def test_playwright_browser_upload_calls_page_set_input_files():
    page = FakePage()
    browser = PlaywrightBrowserController(page=page)

    browser.upload("input[type=file]", "final_video.mp4")

    assert page.actions == [
        ("set_input_files", "input[type=file]", "final_video.mp4"),
    ]


def test_playwright_browser_preserves_call_order():
    page = FakePage()
    browser = PlaywrightBrowserController(page=page)

    browser.open("https://studio.youtube.com")
    browser.upload("input[type=file]", "final_video.mp4")
    browser.fill("input[name=title]", "猫の意外な雑学")
    browser.click("button[data-test-id=draft-save]")

    assert page.actions == [
        ("goto", "https://studio.youtube.com"),
        ("set_input_files", "input[type=file]", "final_video.mp4"),
        ("fill", "input[name=title]", "猫の意外な雑学"),
        ("click", "button[data-test-id=draft-save]"),
    ]
