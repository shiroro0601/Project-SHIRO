from company.youtube.studio_upload import (
    STATUS_CHANNEL_UNAVAILABLE,
    STATUS_LOGGED_IN,
    STATUS_LOGIN_REQUIRED,
    STATUS_STUDIO_UNAVAILABLE,
    STATUS_UNKNOWN,
    YouTubeStudioLoginChecker,
)


class FakeBrowser:
    def __init__(self, current_url, visible=None):
        self.current_url = current_url
        self.visible = set(visible or [])

    def is_visible(self, selector):
        return selector in self.visible


def test_login_checker_detects_logged_in_studio():
    browser = FakeBrowser(
        "https://studio.youtube.com/",
        visible={"ytcp-button#create-icon"},
    )

    result = YouTubeStudioLoginChecker().check(browser)

    assert result.status == STATUS_LOGGED_IN
    assert result.logged_in is True


def test_login_checker_detects_google_sign_in():
    browser = FakeBrowser("https://accounts.google.com/signin")

    result = YouTubeStudioLoginChecker().check(browser)

    assert result.status == STATUS_LOGIN_REQUIRED
    assert result.logged_in is False


def test_login_checker_detects_channel_unavailable():
    browser = FakeBrowser(
        "https://studio.youtube.com/",
        visible={"text=Create a channel"},
    )

    result = YouTubeStudioLoginChecker().check(browser)

    assert result.status == STATUS_CHANNEL_UNAVAILABLE
    assert result.logged_in is False


def test_login_checker_detects_studio_unavailable():
    browser = FakeBrowser("https://example.com/")

    result = YouTubeStudioLoginChecker().check(browser)

    assert result.status == STATUS_STUDIO_UNAVAILABLE


def test_login_checker_returns_unknown_when_studio_ui_is_not_detected():
    browser = FakeBrowser("https://studio.youtube.com/")

    result = YouTubeStudioLoginChecker().check(browser)

    assert result.status == STATUS_UNKNOWN
    assert result.logged_in is False
