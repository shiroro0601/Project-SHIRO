from dataclasses import dataclass

from company.youtube.studio_upload import (
    YouTubeMetadataPreparationResult,
    YouTubePrivateSaveConfirmer,
    YouTubePrivateSavePolicy,
    YouTubeStudioSelectors,
    YouTubeVideoMetadata,
)


class FakePrivateSaveBrowser:
    def __init__(
        self,
        *,
        next_clicks_to_visibility=3,
        private_exists=True,
        private_checked_after_click=True,
        save_enabled=True,
        save_completes=True,
        checks_error=False,
        publish_visible=False,
        video_url="https://youtu.be/private-video",
    ):
        self.next_clicks_to_visibility = next_clicks_to_visibility
        self.private_exists = private_exists
        self.private_checked_after_click = private_checked_after_click
        self.save_enabled = save_enabled
        self.save_completes = save_completes
        self.checks_error = checks_error
        self.publish_visible = publish_visible
        self.video_url = video_url
        self.actions = []
        self.next_clicks = 0
        self.private_checked = False
        self.current_url = "https://studio.youtube.com/upload"

    def is_visible(self, selector):
        if "非公開として保存済み" in selector or "Saved as private" in selector:
            return self.save_completes
        if "Publish" in selector:
            return self.publish_visible
        if "Error" in selector or "エラー" in selector or "Copyright issue" in selector:
            return self.checks_error
        if "ytcp-video-visibility-select" in selector or "公開設定" in selector or "Visibility" in selector:
            return self.next_clicks >= self.next_clicks_to_visibility
        if "Private" in selector or "非公開" in selector:
            return self.private_exists and self.next_clicks >= self.next_clicks_to_visibility
        return False

    def wait_for_visible(self, selector):
        return self.is_visible(selector) or (self.save_completes and "Saved" in selector)

    def wait_for_hidden(self, selector):
        return self.save_completes and "ytcp-uploads-dialog" in selector

    def click_first_enabled(self, selectors):
        first = selectors[0]
        self.actions.append(("click_first_enabled", first))
        if "Next" in str(selectors) or "次へ" in str(selectors):
            self.next_clicks += 1
            return True
        if "done-button" in str(selectors) or "保存" in str(selectors) or "SAVE" in str(selectors):
            if not self.save_enabled:
                return False
            self.actions.append(("save", first))
            return True
        return False

    def click_first(self, selectors):
        first = selectors[0]
        self.actions.append(("click_first", first))
        if "Private" in str(selectors) or "非公開" in str(selectors):
            if not self.private_exists:
                return False
            self.private_checked = self.private_checked_after_click
            return True
        return False

    def is_checked(self, selectors):
        return self.private_checked

    def is_enabled(self, selectors):
        return self.save_enabled

    def read_href(self, selectors):
        return self.video_url


@dataclass
class FakeMetadataPreparer:
    browser: FakePrivateSaveBrowser
    status: str = "metadata_prepared"

    def __post_init__(self):
        self.upload_preparer = type("UploadPreparer", (), {"browser": self.browser})()
        self.selectors = YouTubeStudioSelectors()

    def prepare_metadata(self, video_path, metadata, keep_open=False, input_func=input):
        return YouTubeMetadataPreparationResult(
            status=self.status,
            video_path=video_path,
            title=metadata.title,
            description=metadata.description,
            made_for_kids=metadata.made_for_kids,
            tags=metadata.tags,
            title_applied=self.status == "metadata_prepared",
            description_applied=self.status == "metadata_prepared",
            audience_applied=self.status == "metadata_prepared",
            tags_applied=self.status == "metadata_prepared",
            saved=False,
            published=False,
            error="" if self.status == "metadata_prepared" else self.status,
        )


def metadata():
    return YouTubeVideoMetadata(
        title="Project SHIRO Private Smoke Test",
        description="非公開保存テスト",
        made_for_kids=False,
        tags=("ProjectSHIRO",),
    )


def confirmer(browser, status="metadata_prepared"):
    return YouTubePrivateSaveConfirmer(FakeMetadataPreparer(browser, status=status))


def test_confirm_flag_is_required_and_save_is_not_clicked():
    browser = FakePrivateSaveBrowser()

    result = confirmer(browser).save_private("video.mp4", metadata())

    assert result.status == "confirmation_required"
    assert result.saved is False
    assert result.published is False
    assert result.save_clicked is False
    assert not any(action[0] == "save" for action in browser.actions)


def test_private_save_success_clicks_next_private_and_save_once():
    browser = FakePrivateSaveBrowser()

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "private_saved"
    assert result.private_selected is True
    assert result.save_clicked is True
    assert result.saved is True
    assert result.published is False
    assert result.privacy_status == "private"
    assert result.video_url == "https://youtu.be/private-video"
    assert sum(1 for action in browser.actions if action[0] == "save") == 1
    assert not any("Public" in str(action) or "Unlisted" in str(action) for action in browser.actions)
    assert not any("Schedule" in str(action) or "Publish" in str(action) for action in browser.actions)
    assert result.evidence.private_checked_before_click is True
    assert result.evidence.save_button_enabled is True
    assert result.evidence.click_dispatched is True
    assert result.evidence.dialog_closed is True
    assert result.evidence.completion_confirmed is True


def test_keep_open_eof_after_success_does_not_fail_result():
    browser = FakePrivateSaveBrowser()

    def eof_input(_message):
        raise EOFError

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
        keep_open=True,
        input_func=eof_input,
    )

    assert result.status == "private_saved"
    assert result.saved is True
    assert result.published is False


def test_private_option_missing_stops_before_save():
    browser = FakePrivateSaveBrowser(private_exists=False)

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "private_option_not_found"
    assert result.saved is False
    assert result.save_clicked is False


def test_private_selection_failure_stops_before_save():
    browser = FakePrivateSaveBrowser(private_checked_after_click=False)

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "private_selection_failed"
    assert result.saved is False
    assert result.save_clicked is False


def test_checks_error_stops_before_visibility_and_save():
    browser = FakePrivateSaveBrowser(checks_error=True)

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "checks_failed"
    assert result.saved is False
    assert result.save_clicked is False


def test_max_next_clicks_prevents_infinite_loop():
    browser = FakePrivateSaveBrowser(next_clicks_to_visibility=10)

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True, max_next_clicks=2),
    )

    assert result.status == "next_step_timeout"
    assert result.saved is False


def test_save_disabled_fails_without_save_click():
    browser = FakePrivateSaveBrowser(save_enabled=False)

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "save_button_disabled"
    assert result.saved is False
    assert result.save_clicked is False


def test_save_completion_timeout_is_failure_after_single_save_click():
    browser = FakePrivateSaveBrowser(save_completes=False)

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "save_unverified"
    assert result.saved is False
    assert result.save_clicked is True
    assert sum(1 for action in browser.actions if action[0] == "save") == 1
    assert result.evidence.click_dispatched is True
    assert result.evidence.completion_confirmed is False


def test_dialog_close_only_is_not_confirmed_without_video_id():
    browser = FakePrivateSaveBrowser(video_url="")

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "save_unverified"
    assert result.saved is False
    assert result.save_clicked is True
    assert result.evidence.dialog_closed is True
    assert result.evidence.post_click_video_id == ""
    assert result.evidence.completion_confirmed is False


def test_success_toast_only_is_not_confirmed_without_video_id():
    class ToastOnlyBrowser(FakePrivateSaveBrowser):
        def wait_for_hidden(self, selector):
            return False

        def wait_for_visible(self, selector):
            return "Saved" in selector or "保存済み" in selector

    browser = ToastOnlyBrowser(video_url="")

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "save_unverified"
    assert result.evidence.success_message_detected is True
    assert result.evidence.completion_confirmed is False


def test_video_id_without_private_confirmation_is_not_confirmed():
    class PrivateLostBrowser(FakePrivateSaveBrowser):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.checked_calls = 0

        def is_checked(self, selectors):
            self.checked_calls += 1
            return self.checked_calls < 3 and self.private_checked

    browser = PrivateLostBrowser(video_url="https://youtu.be/private-video")

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "save_unverified"
    assert result.evidence.post_click_video_id == "private-video"
    assert result.evidence.post_click_private_visibility_detected is False
    assert result.evidence.completion_confirmed is False


def test_publish_visible_is_rejected_before_save():
    browser = FakePrivateSaveBrowser(publish_visible=True)

    result = confirmer(browser).save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "unexpected_publish_state"
    assert result.saved is False
    assert result.published is False
    assert result.save_clicked is False


def test_metadata_failure_is_returned_without_save():
    browser = FakePrivateSaveBrowser()

    result = confirmer(browser, status="metadata_failed").save_private(
        "video.mp4",
        metadata(),
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
    )

    assert result.status == "metadata_failed"
    assert result.saved is False
    assert not any(action[0] == "save" for action in browser.actions)
