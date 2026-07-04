from company.automation.browser import FakeBrowserController
from main_v13_youtube_studio_open_check import run_youtube_studio_open_check


def test_youtube_studio_open_check_returns_opened_status():
    browser = FakeBrowserController()

    result = run_youtube_studio_open_check(browser)

    assert result["status"] == "opened"


def test_youtube_studio_open_check_returns_url():
    browser = FakeBrowserController()

    result = run_youtube_studio_open_check(browser)

    assert result["url"] == "https://studio.youtube.com"


def test_youtube_studio_open_check_records_only_open_action():
    browser = FakeBrowserController()

    run_youtube_studio_open_check(browser)

    assert browser.actions == [("open", "https://studio.youtube.com")]


def test_youtube_studio_open_check_accepts_custom_url():
    browser = FakeBrowserController()

    result = run_youtube_studio_open_check(
        browser,
        url="https://studio.youtube.com/channel",
    )

    assert result["url"] == "https://studio.youtube.com/channel"
    assert browser.actions == [("open", "https://studio.youtube.com/channel")]


def test_youtube_studio_open_check_does_not_upload_fill_or_click():
    browser = FakeBrowserController()

    run_youtube_studio_open_check(browser)

    action_names = [action[0] for action in browser.actions]
    assert "upload" not in action_names
    assert "fill" not in action_names
    assert "click" not in action_names
