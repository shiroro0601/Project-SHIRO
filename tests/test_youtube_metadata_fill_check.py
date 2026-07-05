import pytest

from company.automation.browser import FakeBrowserController
from main_v13_youtube_metadata_fill_check import (
    run_youtube_metadata_fill_check,
)


def test_youtube_metadata_fill_check_records_actions():
    browser = FakeBrowserController()

    result = run_youtube_metadata_fill_check(
        browser,
        "test.mp4",
        {
            "title": "Test Title",
            "description": "Test Description",
            "tags": ["AI", "Shorts"],
        },
    )

    assert result["status"] == "metadata_filled"
    assert result["video_path"] == "test.mp4"
    assert result["title"] == "Test Title"

    assert browser.actions == [
        ("open", "https://studio.youtube.com"),
        ("click", "ytcp-button#create-icon"),
        ("click", "tp-yt-paper-item#text-item-0"),
        ("upload", "input[type=file]", "test.mp4"),
        ("fill", "input[name=title]", "Test Title"),
        ("fill", "textarea[name=description]", "Test Description"),
        ("fill", "input[name=tags]", "AI,Shorts"),
    ]


def test_metadata_fill_rejects_empty_video_path():
    browser = FakeBrowserController()

    with pytest.raises(ValueError):
        run_youtube_metadata_fill_check(
            browser,
            "",
            {"title": "Test Title"},
        )


def test_metadata_fill_rejects_missing_title():
    browser = FakeBrowserController()

    with pytest.raises(ValueError):
        run_youtube_metadata_fill_check(
            browser,
            "test.mp4",
            {},
        )


def test_metadata_fill_does_not_publish():
    browser = FakeBrowserController()

    run_youtube_metadata_fill_check(
        browser,
        "test.mp4",
        {
            "title": "Test Title",
            "description": "Test Description",
        },
    )

    actions = [action[0] for action in browser.actions]

    assert "publish" not in actions
    assert actions.count("click") == 2