from dataclasses import dataclass

from company.youtube.studio_upload import (
    UploadPreparationResult,
    YouTubeMetadataPreparer,
    YouTubeStudioUploadPreparer,
    YouTubeVideoMetadata,
)


class FakeBrowser:
    def __init__(self, *, show_more_selector="text=SHOW MORE", fail_title=False):
        self.values = {}
        self.checked = {}
        self.tags = ()
        self.actions = []
        self.show_more_selector = show_more_selector
        self.fail_title = fail_title

    def fill_text(self, selectors, value):
        self.actions.append(("fill_text", selectors[0], value))
        if self.fail_title and selectors[0] == "input[name=title]":
            return False
        self.values[selectors[0]] = value
        return True

    def read_text(self, selectors):
        return self.values.get(selectors[0], "")

    def click_first(self, selectors):
        self.actions.append(("click_first", selectors[0]))
        if self.show_more_selector in selectors:
            return True
        selector = selectors[0]
        self.checked[selector] = True
        return True

    def is_checked(self, selectors):
        return bool(self.checked.get(selectors[0], False))

    def is_visible(self, selector):
        return selector == "input[aria-label='Tags']"

    def add_tags(self, selectors, tags):
        self.actions.append(("add_tags", selectors[0], tags))
        self.tags = tuple(tags)
        return True

    def read_tags(self, chip_selectors, input_selectors):
        return self.tags


class TrailingNewlineBrowser(FakeBrowser):
    def read_text(self, selectors):
        value = super().read_text(selectors)
        if selectors[0] == "textarea[name=description]":
            return value + "\n"
        return value


@dataclass
class FakeUploadPreparer:
    browser: FakeBrowser
    status: str = "prepared"

    def __post_init__(self):
        self.selectors = YouTubeStudioUploadPreparer(browser=self.browser).selectors
        self.called = False

    def prepare_upload(self, video_path, keep_open=False):
        self.called = True
        return UploadPreparationResult(
            status=self.status,
            video_path=video_path,
            filename="video.mp4",
            upload_started=self.status == "prepared",
            details_visible=self.status == "prepared",
            logged_in=True,
            current_url="https://studio.youtube.com/",
            saved=False,
            published=False,
            error="" if self.status == "prepared" else "not prepared",
        )


def metadata(made_for_kids=False):
    return YouTubeVideoMetadata(
        title="猫の意外な雑学",
        description="猫に関する説明\n改行あり",
        made_for_kids=made_for_kids,
        tags=("猫", "雑学"),
    )


def test_metadata_preparer_reuses_upload_preparation_and_applies_fields():
    browser = FakeBrowser()
    upload_preparer = FakeUploadPreparer(browser)

    result = YouTubeMetadataPreparer(upload_preparer).prepare_metadata(
        "video.mp4",
        metadata(made_for_kids=False),
    )

    assert upload_preparer.called is True
    assert result.status == "metadata_prepared"
    assert result.title_applied is True
    assert result.description_applied is True
    assert result.audience_applied is True
    assert result.tags_applied is True
    assert result.saved is False
    assert result.published is False
    assert ("add_tags", "input[aria-label='Tags']", ("猫", "雑学")) in browser.actions
    assert not any("draft-save" in str(action) for action in browser.actions)
    assert not any("Publish" in str(action) for action in browser.actions)
    assert not any("visibility" in str(action).lower() for action in browser.actions)


def test_metadata_preparer_applies_made_for_kids_true():
    browser = FakeBrowser()
    result = YouTubeMetadataPreparer(FakeUploadPreparer(browser)).prepare_metadata(
        "video.mp4",
        metadata(made_for_kids=True),
    )

    assert result.audience_applied is True
    assert any("MFK" in str(action) for action in browser.actions)


def test_metadata_preparer_keeps_description_newlines():
    browser = FakeBrowser()
    result = YouTubeMetadataPreparer(FakeUploadPreparer(browser)).prepare_metadata(
        "video.mp4",
        metadata(),
    )

    assert result.description == "猫に関する説明\n改行あり"
    assert browser.values["textarea[name=description]"] == "猫に関する説明\n改行あり"


def test_metadata_preparer_accepts_youtube_description_terminal_newline():
    browser = TrailingNewlineBrowser()
    result = YouTubeMetadataPreparer(FakeUploadPreparer(browser)).prepare_metadata(
        "video.mp4",
        metadata(),
    )

    assert result.status == "metadata_prepared"
    assert result.description_applied is True


def test_metadata_preparer_supports_japanese_show_more():
    browser = FakeBrowser(show_more_selector="text=すべて表示")

    result = YouTubeMetadataPreparer(FakeUploadPreparer(browser)).prepare_metadata(
        "video.mp4",
        metadata(),
    )

    assert result.status == "metadata_prepared"


def test_metadata_preparer_supports_japanese_more_button():
    browser = FakeBrowser(show_more_selector="text=もっと見る")

    result = YouTubeMetadataPreparer(FakeUploadPreparer(browser)).prepare_metadata(
        "video.mp4",
        metadata(),
    )

    assert result.status == "metadata_prepared"


def test_metadata_preparer_returns_failure_without_saving_when_title_missing():
    browser = FakeBrowser(fail_title=True)

    result = YouTubeMetadataPreparer(FakeUploadPreparer(browser)).prepare_metadata(
        "video.mp4",
        metadata(),
    )

    assert result.status == "title_input_not_found"
    assert result.saved is False
    assert result.published is False
    assert not any("draft-save" in str(action) for action in browser.actions)


def test_metadata_preparer_stops_when_upload_preparation_fails():
    browser = FakeBrowser()
    result = YouTubeMetadataPreparer(
        FakeUploadPreparer(browser, status="login_required")
    ).prepare_metadata("video.mp4", metadata())

    assert result.status == "login_required"
    assert result.title_applied is False
    assert result.saved is False
    assert result.published is False
