from company.automation.browser import FakeBrowserController
from main_v13_youtube_upload_page_open_check import (
    run_youtube_upload_page_open_check,
)


def test_youtube_upload_page_open_check_returns_upload_page_opened_status():
    browser = FakeBrowserController()

    result = run_youtube_upload_page_open_check(browser)

    assert result["status"] == "upload_page_opened"


def test_youtube_upload_page_open_check_returns_url():
    browser = FakeBrowserController()

    result = run_youtube_upload_page_open_check(browser)

    assert result["url"] == "https://studio.youtube.com"


def test_youtube_upload_page_open_check_records_open_action():
    browser = FakeBrowserController()

    run_youtube_upload_page_open_check(browser)

    assert ("open", "https://studio.youtube.com") in browser.actions


def test_youtube_upload_page_open_check_records_two_click_actions():
    browser = FakeBrowserController()

    run_youtube_upload_page_open_check(browser)

    click_actions = [action for action in browser.actions if action[0] == "click"]
    assert click_actions == [
        ("click", "ytcp-button#create-icon"),
        ("click", "tp-yt-paper-item#text-item-0"),
    ]


def test_youtube_upload_page_open_check_does_not_upload_or_fill():
    browser = FakeBrowserController()

    run_youtube_upload_page_open_check(browser)

    action_names = [action[0] for action in browser.actions]
    assert "upload" not in action_names
    assert "fill" not in action_names


def test_youtube_upload_page_open_check_records_actions_in_order():
    browser = FakeBrowserController()

    run_youtube_upload_page_open_check(browser)

    assert browser.actions == [
        ("open", "https://studio.youtube.com"),
        ("click", "ytcp-button#create-icon"),
        ("click", "tp-yt-paper-item#text-item-0"),
    ]


def test_youtube_upload_page_open_check_accepts_custom_url():
    browser = FakeBrowserController()

    result = run_youtube_upload_page_open_check(
        browser,
        url="https://studio.youtube.com/channel",
    )

    assert result["url"] == "https://studio.youtube.com/channel"
    assert browser.actions[0] == ("open", "https://studio.youtube.com/channel")
