import pytest

from company.automation.browser import FakeBrowserController

from main_v13_youtube_draft_save_check import (
    run_youtube_draft_save_check,
)


def test_youtube_draft_save():

    browser = FakeBrowserController()

    result = run_youtube_draft_save_check(
        browser,
        "test.mp4",
        {
            "title": "Test",
            "description": "Description",
        },
    )

    assert result["status"] == "draft_saved"

    actions = [
        action[0]
        for action in browser.actions
    ]

    assert "open" in actions
    assert "upload" in actions
    assert "fill" in actions
    assert "click" in actions


def test_no_publish_action():

    browser = FakeBrowserController()

    run_youtube_draft_save_check(
        browser,
        "test.mp4",
        {"title": "Test"},
    )

    actions = str(browser.actions)

    assert "publish" not in actions


def test_empty_video_path():

    browser = FakeBrowserController()

    with pytest.raises(ValueError):
        run_youtube_draft_save_check(
            browser,
            "",
            {"title": "Test"},
        )


def test_missing_title():

    browser = FakeBrowserController()

    with pytest.raises(ValueError):
        run_youtube_draft_save_check(
            browser,
            "test.mp4",
            {},
        )