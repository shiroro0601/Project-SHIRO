from company.youtube.studio_upload import (
    YouTubeRecentContentInspector,
    YouTubeRecentContentInspectorConfig,
)


class FakeRecentContentBrowser:
    def __init__(self, rows_by_url=None):
        self.rows_by_url = rows_by_url or {}
        self.opened_urls = []
        self.actions = []
        self.current_url = "https://studio.youtube.com/channel/CHANNEL"

    def open(self, url):
        self.actions.append(("open", url))
        self.opened_urls.append(url)
        self.current_url = url

    def collect_video_rows(self, selectors):
        self.actions.append(("collect_video_rows", selectors))
        return list(self.rows_by_url.get(self.current_url, []))

    def upload(self, *args):
        self.actions.append(("upload", args))

    def fill_text(self, *args):
        self.actions.append(("fill_text", args))

    def click_first(self, *args):
        self.actions.append(("click_first", args))

    def click_first_enabled(self, *args):
        self.actions.append(("click_first_enabled", args))


def row(title, privacy="非公開", href="/video/abc123/edit", extra="2026/07/13"):
    return {"text": f"12:34\n{title}\n{privacy}\n{extra}", "href": href}


def inspect(rows_by_url, target_title="Project SHIRO Private Smoke Test", **config):
    browser = FakeRecentContentBrowser(rows_by_url)
    result = YouTubeRecentContentInspector(
        browser=browser,
        inspector_config=YouTubeRecentContentInspectorConfig(**config),
        sleeper=lambda _seconds: None,
    ).inspect(target_title=target_title)
    return browser, result


def test_inspector_collects_videos_shorts_live_and_drafts_rows():
    rows_by_url = {
        "https://studio.youtube.com/channel/CHANNEL/videos/upload": [row("Video One")],
        "https://studio.youtube.com/channel/CHANNEL/videos/shorts": [row("Short One")],
        "https://studio.youtube.com/channel/CHANNEL/videos/live": [row("Live One")],
        "https://studio.youtube.com/channel/CHANNEL/videos/drafts": [
            row("Draft One", "下書き")
        ],
    }

    browser, result = inspect(rows_by_url)

    assert result.status == "inspected"
    assert result.checked_locations == ("video", "short", "live", "draft")
    assert {record.content_type for record in result.records} == {
        "video",
        "short",
        "live",
        "draft",
    }
    assert any(url.endswith("/videos/upload") for url in browser.opened_urls)
    assert any(url.endswith("/videos/shorts") for url in browser.opened_urls)
    assert any(url.endswith("/videos/live") for url in browser.opened_urls)
    assert any(url.endswith("/videos/drafts") for url in browser.opened_urls)


def test_inspector_respects_total_and_per_location_limits():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    shorts_url = "https://studio.youtube.com/channel/CHANNEL/videos/shorts"
    rows_by_url = {
        upload_url: [row(f"Video {index}", href=f"/video/v{index}/edit") for index in range(5)],
        shorts_url: [row(f"Short {index}", href=f"/video/s{index}/edit") for index in range(5)],
    }

    _, result = inspect(rows_by_url, max_items=3, max_items_per_location=2)

    assert result.total_records == 3
    assert [record.title for record in result.records] == ["Video 0", "Video 1", "Short 0"]


def test_inspector_handles_empty_lists():
    _, result = inspect({})

    assert result.status == "inspected"
    assert result.total_records == 0
    assert result.records == ()


def test_inspector_extracts_title_visibility_processing_video_id_url_and_date():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    _, result = inspect(
        {
            upload_url: [
                row(
                    "Project SHIRO Private Smoke Test",
                    "処理中",
                    "/video/abc123/edit",
                    "2026/07/13",
                )
            ]
        }
    )

    record = result.records[0]
    assert record.title == "Project SHIRO Private Smoke Test"
    assert record.privacy_status == "processing"
    assert record.processing_status == "processing"
    assert record.video_id == "abc123"
    assert record.video_url == "https://www.youtube.com/watch?v=abc123"
    assert record.studio_url.endswith("/video/abc123/edit")
    assert record.displayed_date == "2026/07/13"


def test_inspector_keeps_rows_without_video_id():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    _, result = inspect({upload_url: [row("No ID", "非公開", "")]})

    assert result.total_records == 1
    assert result.records[0].video_id == ""
    assert result.records_without_video_id == 1
    assert result.no_video_id_candidates == result.records


def test_inspector_classifies_title_and_keyword_candidates():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    _, result = inspect(
        {
            upload_url: [
                row("Project SHIRO Private Smoke Test"),
                row("  project   shiro private smoke test  ", href="/video/def456/edit"),
                row("Project SHIRO candidate", href="/video/project/edit"),
                row("Smoke Test candidate", href="/video/smoke/edit"),
                row("Prefix Project SHIRO Private Smoke Test suffix", href="/video/partial/edit"),
            ]
        }
    )

    assert [record.title for record in result.exact_matches] == [
        "Project SHIRO Private Smoke Test"
    ]
    assert [record.video_id for record in result.normalized_matches] == ["def456"]
    assert [record.video_id for record in result.partial_matches] == ["partial"]
    assert len(result.project_shiro_candidates) == 4
    assert len(result.smoke_test_candidates) == 4


def test_inspector_classifies_private_draft_processing_and_empty_title_candidates():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    _, result = inspect(
        {
            upload_url: [
                row("Private One", "非公開", "/video/p/edit"),
                row("Draft One", "下書き", "/video/d/edit"),
                row("Processing One", "処理中", "/video/pr/edit"),
                {"text": "12:34\n非公開\n2026/07/13", "href": ""},
            ]
        }
    )

    assert len(result.private_recent_candidates) == 2
    assert len(result.draft_candidates) == 1
    assert len(result.processing_candidates) == 1
    assert len(result.empty_title_candidates) == 1
    assert result.private_count == 2
    assert result.draft_count == 1
    assert result.processing_count == 1


def test_inspector_does_not_execute_write_actions():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    browser, _ = inspect({upload_url: [row("Read Only")]})

    action_names = [action[0] for action in browser.actions]
    assert "upload" not in action_names
    assert "fill_text" not in action_names
    assert "click_first" not in action_names
    assert "click_first_enabled" not in action_names
