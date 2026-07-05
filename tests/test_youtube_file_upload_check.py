import pytest

from company.automation.browser import FakeBrowserController
from main_v13_youtube_file_upload_check import (
    run_youtube_file_upload_check,
)


def test_youtube_file_upload_check():
    browser = FakeBrowserController()

    result = run_youtube_file_upload_check(
        browser,
        "test.mp4",
    )

    assert result["status"] == "file_selected"
    assert result["video_path"] == "test.mp4"

    assert browser.actions == [
        (
            "open",
            "https://studio.youtube.com",
        ),
        (
            "click",
            "ytcp-button#create-icon",
        ),
        (
            "click",
            "tp-yt-paper-item#text-item-0",
        ),
        (
            "upload",
            "input[type=file]",
            "test.mp4",
        ),
    ]


def test_file_upload_check_rejects_empty_video_path():
    browser = FakeBrowserController()

    with pytest.raises(ValueError):
        run_youtube_file_upload_check(
            browser,
            "",
        )


def test_file_upload_check_does_not_fill_or_publish():
    browser = FakeBrowserController()

    run_youtube_file_upload_check(
        browser,
        "test.mp4",
    )

    actions = [
        action[0]
        for action in browser.actions
    ]

    assert "fill" not in actions