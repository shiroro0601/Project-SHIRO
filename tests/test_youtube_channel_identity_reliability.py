from company.youtube.studio_upload import (
    YouTubeCDPConfig,
    YouTubeStudioChannelIdentityReader,
)


class FakeBrowser:
    def __init__(self, names=None, url="https://studio.youtube.com/"):
        self.names = tuple(names or ())
        self.current_url = url
        self.open_calls = []
        self.wait_calls = []
        self.close_called = False
        self.upload_called = False
        self.save_called = False

    def open(self, url):
        self.open_calls.append(url)
        self.current_url = url

    def wait_for_visible(self, selector):
        self.wait_calls.append(selector)
        return selector == "ytcp-app"

    def read_channel_names(self, selectors):
        return self.names

    def close(self):
        self.close_called = True


def test_identity_reader_accepts_exact_expected_match_after_normalization():
    browser = FakeBrowser(["  恋愛らぼっ‼  ", "恋愛らぼっ‼"])

    identity = YouTubeStudioChannelIdentityReader(browser=browser).read_identity(
        "恋愛らぼっ‼"
    )

    assert identity.identity_confirmed is True
    assert identity.channel_name == "恋愛らぼっ‼"
    assert browser.upload_called is False
    assert browser.save_called is False


def test_identity_reader_rejects_partial_match():
    browser = FakeBrowser(["恋愛らぼ"])

    identity = YouTubeStudioChannelIdentityReader(browser=browser).read_identity(
        "恋愛らぼっ‼"
    )

    assert identity.identity_confirmed is False
    assert identity.error == "channel_mismatch"


def test_identity_reader_uses_aria_or_dashboard_fallback_candidates():
    browser = FakeBrowser(["", "  恋愛らぼっ‼  "])

    identity = YouTubeStudioChannelIdentityReader(browser=browser).read_identity(
        "恋愛らぼっ‼"
    )

    assert identity.identity_confirmed is True


def test_identity_reader_returns_unverified_when_no_name():
    browser = FakeBrowser([])

    identity = YouTubeStudioChannelIdentityReader(browser=browser).read_identity(
        "恋愛らぼっ‼"
    )

    assert identity.identity_confirmed is False
    assert identity.error == "identity_unverified"


def test_identity_reader_extracts_channel_id_from_safe_url():
    browser = FakeBrowser(
        ["恋愛らぼっ‼"],
        url="https://studio.youtube.com/channel/UC123/videos",
    )

    identity = YouTubeStudioChannelIdentityReader(
        browser=browser,
        config=YouTubeCDPConfig(studio_url="https://studio.youtube.com/channel/UC123/videos"),
    ).read_identity("恋愛らぼっ‼")

    assert identity.channel_id == "UC123"
    assert identity.identity_confirmed is True


def test_identity_reader_does_not_close_injected_browser():
    browser = FakeBrowser(["恋愛らぼっ‼"])

    YouTubeStudioChannelIdentityReader(browser=browser).read_identity("恋愛らぼっ‼")

    assert browser.close_called is False
