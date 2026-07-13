from company.youtube.studio_upload import (
    YouTubePrivateSaveVerificationResult,
    YouTubePrivateSaveVerifierConfig,
    YouTubePrivateSaveVerifier,
)


class FakeReadOnlyBrowser:
    def __init__(self, rows_by_url=None):
        self.rows_by_url = rows_by_url or {}
        self.opened_urls = []
        self.actions = []
        self.current_url = "https://studio.youtube.com/channel/CHANNEL"
        self.scrolls = 0

    def open(self, url):
        self.opened_urls.append(url)
        self.current_url = url

    def search_text(self, selectors, value):
        self.actions.append(("search_text", selectors, value))
        return True

    def collect_video_rows(self, selectors):
        self.actions.append(("collect_video_rows", selectors))
        return list(self.rows_by_url.get(self.current_url, []))

    def scroll_content(self):
        self.actions.append(("scroll_content",))
        self.scrolls += 1


def row(title, privacy="非公開", href="/video/abc123/edit"):
    return {"text": f"12:34\n{title}\n{privacy}\n説明", "href": href}


def test_verification_result_can_represent_private_match():
    result = YouTubePrivateSaveVerificationResult(
        status="verified_private",
        found=True,
        title="Title",
        title_matched=True,
        privacy_status="private",
        private_confirmed=True,
        duplicate_count=1,
        video_id="abc123",
        content_type="video",
    )

    assert result.status == "verified_private"
    assert result.private_confirmed is True
    assert result.video_id == "abc123"
    assert result.content_type == "video"


def test_verifier_opens_upload_and_shorts_lists_read_only():
    browser = FakeReadOnlyBrowser()

    YouTubePrivateSaveVerifier(
        browser=browser,
        verifier_config=YouTubePrivateSaveVerifierConfig(timeout_seconds=0),
    ).verify("Missing")

    assert any(url.endswith("/videos/upload") for url in browser.opened_urls)
    assert any(url.endswith("/videos/shorts") for url in browser.opened_urls)
    assert any(url.endswith("/videos/live") for url in browser.opened_urls)
    assert any(url.endswith("/videos/drafts") for url in browser.opened_urls)
    assert any(action[0] == "search_text" for action in browser.actions)
    assert not any("upload" == action[0] for action in browser.actions)
    assert not any("save" == action[0] for action in browser.actions)
    assert not any("publish" == action[0] for action in browser.actions)


def test_verifier_finds_exact_japanese_private_title():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    browser = FakeReadOnlyBrowser(
        {upload_url: [row("Project SHIRO Private Smoke Test", "非公開")]}
    )

    result = YouTubePrivateSaveVerifier(browser=browser).verify(
        "Project SHIRO Private Smoke Test"
    )

    assert result.status == "verified_private"
    assert result.found is True
    assert result.title_matched is True
    assert result.privacy_status == "private"
    assert result.private_confirmed is True
    assert result.duplicate_count == 1
    assert result.match_type == "exact"
    assert result.video_id == "abc123"
    assert result.content_type == "video"
    assert "video" in result.checked_locations
    assert result.studio_url.endswith("/video/abc123/edit")
    assert result.video_url == "https://www.youtube.com/watch?v=abc123"


def test_verifier_finds_private_english_ui():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    browser = FakeReadOnlyBrowser({upload_url: [row("Smoke Title", "Private")]})

    result = YouTubePrivateSaveVerifier(browser=browser).verify("Smoke Title")

    assert result.status == "verified_private"
    assert result.private_confirmed is True
    assert result.match_type == "exact"


def test_verifier_can_find_shorts_tab_candidate():
    shorts_url = "https://studio.youtube.com/channel/CHANNEL/videos/shorts"
    browser = FakeReadOnlyBrowser({shorts_url: [row("Short Smoke", "非公開")]})

    result = YouTubePrivateSaveVerifier(browser=browser).verify("Short Smoke")

    assert result.status == "verified_private"
    assert any(url.endswith("/videos/shorts") for url in browser.opened_urls)
    assert result.content_type == "short"


def test_verifier_returns_not_found_for_missing_title():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    browser = FakeReadOnlyBrowser({upload_url: [row("Other Title", "非公開")]})

    result = YouTubePrivateSaveVerifier(
        browser=browser,
        verifier_config=YouTubePrivateSaveVerifierConfig(timeout_seconds=0),
    ).verify("Missing")

    assert result.status == "not_found"
    assert result.found is False
    assert result.private_confirmed is False


def test_verifier_returns_duplicate_candidates_for_multiple_exact_matches():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    browser = FakeReadOnlyBrowser(
        {upload_url: [row("Same Title", "非公開"), row("Same Title", "非公開", "/video/def456/edit")]}
    )

    result = YouTubePrivateSaveVerifier(browser=browser).verify("Same Title")

    assert result.status == "duplicate_candidates"
    assert result.found is True
    assert result.duplicate_count == 2
    assert result.private_confirmed is False


def test_verifier_does_not_accept_public_or_unlisted_matches():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    public = FakeReadOnlyBrowser({upload_url: [row("Title", "Public")]})
    unlisted = FakeReadOnlyBrowser({upload_url: [row("Title", "Unlisted")]})

    public_result = YouTubePrivateSaveVerifier(browser=public).verify("Title")
    unlisted_result = YouTubePrivateSaveVerifier(browser=unlisted).verify("Title")

    assert public_result.status == "visibility_mismatch"
    assert public_result.privacy_status == "public"
    assert public_result.private_confirmed is False
    assert unlisted_result.status == "visibility_mismatch"
    assert unlisted_result.privacy_status == "unlisted"
    assert unlisted_result.private_confirmed is False


def test_verifier_does_not_use_partial_title_match():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    browser = FakeReadOnlyBrowser({upload_url: [row("Project SHIRO Private Smoke Test extended", "非公開")]})

    result = YouTubePrivateSaveVerifier(
        browser=browser,
        verifier_config=YouTubePrivateSaveVerifierConfig(timeout_seconds=0),
    ).verify(
        "Project SHIRO Private Smoke Test"
    )

    assert result.status == "not_found"


def test_verifier_accepts_normalized_exact_title():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    browser = FakeReadOnlyBrowser(
        {upload_url: [row("  Project　SHIRO\nPrivate   Smoke Test  ", "非公開")]}
    )

    result = YouTubePrivateSaveVerifier(browser=browser).verify(
        "Project SHIRO Private Smoke Test"
    )

    assert result.status == "verified_private"
    assert result.match_type == "normalized_exact"


def test_verifier_reports_processing_without_success():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    browser = FakeReadOnlyBrowser({upload_url: [row("Processing Title", "処理中")]})

    result = YouTubePrivateSaveVerifier(
        browser=browser,
        verifier_config=YouTubePrivateSaveVerifierConfig(
            timeout_seconds=0,
            poll_interval_seconds=0,
        ),
    ).verify("Processing Title")

    assert result.status == "verification_timeout"
    assert result.processing is True
    assert result.private_confirmed is False


def test_verifier_polls_after_initial_not_found_with_injected_sleeper():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"

    class PollingBrowser(FakeReadOnlyBrowser):
        def __init__(self):
            super().__init__()
            self.enabled = False

        def collect_video_rows(self, selectors):
            if not self.enabled:
                return []
            return [row("Delayed Title", "非公開")]

    now = {"value": 0.0}
    sleeps = []

    def clock():
        return now["value"]

    browser = PollingBrowser()

    def sleeper(seconds):
        sleeps.append(seconds)
        now["value"] += seconds
        browser.enabled = True

    result = YouTubePrivateSaveVerifier(
        browser=browser,
        verifier_config=YouTubePrivateSaveVerifierConfig(
            timeout_seconds=20,
            poll_interval_seconds=5,
        ),
        clock=clock,
        sleeper=sleeper,
    ).verify("Delayed Title")

    assert result.status == "verified_private"
    assert sleeps == [5]


def test_verifier_limits_candidate_titles():
    upload_url = "https://studio.youtube.com/channel/CHANNEL/videos/upload"
    rows = [row(f"Title {index}", "非公開", f"/video/id{index}/edit") for index in range(20)]
    browser = FakeReadOnlyBrowser({upload_url: rows})

    result = YouTubePrivateSaveVerifier(
        browser=browser,
        verifier_config=YouTubePrivateSaveVerifierConfig(timeout_seconds=0),
    ).verify("Missing")

    assert result.status == "not_found"
    assert len(result.candidate_titles) <= 10


def test_verifier_extracts_video_id_from_watch_and_youtu_be_urls():
    verifier = YouTubePrivateSaveVerifier(browser=FakeReadOnlyBrowser())

    assert verifier._video_id("https://www.youtube.com/watch?v=watch123") == "watch123"
    assert verifier._video_id("https://youtu.be/short123") == "short123"
