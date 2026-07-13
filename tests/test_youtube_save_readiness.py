from company.youtube.studio_upload import (
    YouTubeStudioSelectors,
    YouTubeUploadReadinessChecker,
)


class FakeReadinessBrowser:
    def __init__(
        self,
        *,
        upload_text="100% Uploaded",
        private_checked=True,
        save_enabled=True,
        save_label="保存",
        blocking_error=False,
        current_step="Visibility",
    ):
        self.upload_text = upload_text
        self.private_checked = private_checked
        self.save_enabled = save_enabled
        self.save_label = save_label
        self.blocking_error = blocking_error
        self.current_step = current_step
        self.actions = []

    def is_visible(self, selector):
        self.actions.append(("is_visible", selector))
        if "Error" in selector or "エラー" in selector or "Copyright issue" in selector:
            return self.blocking_error
        if "Upload complete" in selector or "Uploaded" in selector or "完了" in selector:
            return "100%" in self.upload_text or "Complete" in self.upload_text
        if "ytcp-uploads-dialog" in selector:
            return True
        if "done-button" in selector or "保存" in selector or "SAVE" in selector:
            return bool(self.save_label)
        return False

    def read_text(self, selectors):
        text = " ".join(selectors)
        if "progress" in text or "アップロード" in text or "Uploaded" in text:
            return self.upload_text
        if "Error" in text or "エラー" in text or "Copyright issue" in text:
            return "Copyright issue" if self.blocking_error else ""
        if "uploads-dialog" in text:
            return self.current_step
        return ""

    def read_label(self, selectors):
        return self.save_label

    def is_checked(self, selectors):
        return self.private_checked

    def is_enabled(self, selectors):
        return self.save_enabled

    def click(self, *args):
        self.actions.append(("click", args))

    def fill_text(self, *args):
        self.actions.append(("fill_text", args))

    def upload(self, *args):
        self.actions.append(("upload", args))


def check(browser):
    return YouTubeUploadReadinessChecker(YouTubeStudioSelectors()).check(browser)


def test_upload_not_complete_is_not_ready():
    result = check(FakeReadinessBrowser(upload_text="45% Uploaded"))

    assert result.upload_complete is False
    assert result.ready_for_save is False


def test_blocking_error_is_not_ready_and_keeps_error_text():
    result = check(FakeReadinessBrowser(blocking_error=True))

    assert result.blocking_error is True
    assert result.ready_for_save is False
    assert result.error_messages


def test_save_disabled_is_not_ready():
    result = check(FakeReadinessBrowser(save_enabled=False))

    assert result.save_enabled is False
    assert result.ready_for_save is False


def test_upload_complete_private_and_save_enabled_is_ready():
    result = check(FakeReadinessBrowser())

    assert result.upload_complete is True
    assert result.private_checked is True
    assert result.save_enabled is True
    assert result.ready_for_save is True


def test_processing_state_is_distinguished():
    result = check(FakeReadinessBrowser(upload_text="Processing"))

    assert result.processing is True
    assert result.ready_for_save is False


def test_allowed_save_labels_are_exact():
    checker = YouTubeUploadReadinessChecker()

    assert checker.is_allowed_save_label("保存") is True
    assert checker.is_allowed_save_label("SAVE") is True


def test_rejected_save_labels_are_not_allowed():
    checker = YouTubeUploadReadinessChecker()

    for label in ("公開", "PUBLISH", "UNLISTED", "SCHEDULE", "CLOSE", "NEXT"):
        assert checker.is_allowed_save_label(label) is False


def test_readiness_check_is_read_only():
    browser = FakeReadinessBrowser()

    check(browser)

    action_names = [action[0] for action in browser.actions]
    assert "click" not in action_names
    assert "fill_text" not in action_names
    assert "upload" not in action_names
