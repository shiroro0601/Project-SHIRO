import pytest

from company.youtube.studio_upload import (
    YouTubeBrowserConfig,
    YouTubeStudioUploadPreparer,
)


class FakeBrowser:
    def __init__(self, *, logged_in=True):
        self.current_url = "https://studio.youtube.com/"
        self.actions = []
        self.closed = False
        self.visible = {
            "ytcp-button#create-icon",
            "tp-yt-paper-item#text-item-0",
            "input[type=file]",
            "ytcp-uploads-dialog",
            "ytcp-app",
        }
        if not logged_in:
            self.current_url = "https://accounts.google.com/signin"

    def open(self, url):
        self.current_url = url if "accounts" not in self.current_url else self.current_url
        self.actions.append(("open", url))

    def is_visible(self, selector):
        return selector in self.visible

    def click(self, selector):
        self.actions.append(("click", selector))

    def upload(self, selector, file_path):
        self.actions.append(("upload", selector, file_path))

    def wait_for_visible(self, selector):
        self.actions.append(("wait_for_visible", selector))
        return selector in self.visible

    def close(self):
        self.closed = True


class FakeChooserBrowser(FakeBrowser):
    def __init__(self, *, visible_button):
        super().__init__()
        self.visible = {
            "ytcp-button#create-icon",
            "tp-yt-paper-item#text-item-0",
            "ytcp-uploads-dialog",
            "ytcp-app",
            visible_button,
        }
        self.visible_button = visible_button

    def choose_file(self, selectors, file_path):
        for selector in selectors:
            if selector == self.visible_button:
                self.actions.append(("click", selector))
                self.actions.append(("chooser.set_files", file_path))
                return True
        return False


def _video(tmp_path):
    path = tmp_path / "video.mp4"
    path.write_bytes(b"mp4")
    return path


def test_upload_preparation_sets_file_and_never_saves_or_publishes(tmp_path):
    browser = FakeBrowser()
    video_path = _video(tmp_path)

    result = YouTubeStudioUploadPreparer(browser=browser).prepare_upload(str(video_path))

    assert result.status == "prepared"
    assert result.upload_started is True
    assert result.details_visible is True
    assert result.saved is False
    assert result.published is False
    assert result.filename == "video.mp4"
    actions = [action[0] for action in browser.actions]
    assert actions == ["open", "click", "click", "upload", "wait_for_visible"]
    assert ("click", "button[data-test-id=draft-save]") not in browser.actions
    assert not any("Publish" in str(action) for action in browser.actions)
    assert not any("Schedule" in str(action) for action in browser.actions)
    assert not any("public" in str(action).lower() for action in browser.actions)


def test_upload_preparation_prefers_expect_file_chooser_with_japanese_ui(tmp_path):
    browser = FakeChooserBrowser(visible_button="text=ファイルを選択")
    video_path = _video(tmp_path)

    result = YouTubeStudioUploadPreparer(browser=browser).prepare_upload(str(video_path))

    assert result.status == "prepared"
    assert result.saved is False
    assert result.published is False
    assert ("click", "text=ファイルを選択") in browser.actions
    assert ("chooser.set_files", str(video_path.resolve())) in browser.actions
    assert not any(action[0] == "upload" for action in browser.actions)


def test_upload_preparation_prefers_expect_file_chooser_with_english_ui(tmp_path):
    browser = FakeChooserBrowser(visible_button="text=SELECT FILES")
    video_path = _video(tmp_path)

    result = YouTubeStudioUploadPreparer(browser=browser).prepare_upload(str(video_path))

    assert result.status == "prepared"
    assert result.saved is False
    assert result.published is False
    assert ("click", "text=SELECT FILES") in browser.actions
    assert ("chooser.set_files", str(video_path.resolve())) in browser.actions


def test_upload_preparation_keeps_hidden_input_fallback(tmp_path):
    browser = FakeBrowser()
    video_path = _video(tmp_path)

    result = YouTubeStudioUploadPreparer(browser=browser).prepare_upload(str(video_path))

    assert result.status == "prepared"
    assert ("upload", "input[type=file]", str(video_path.resolve())) in browser.actions


def test_upload_preparation_uses_absolute_video_path(tmp_path):
    browser = FakeBrowser()
    video_path = _video(tmp_path)

    result = YouTubeStudioUploadPreparer(browser=browser).prepare_upload(str(video_path))

    upload_action = browser.actions[3]
    assert upload_action[0] == "upload"
    assert upload_action[2] == str(video_path.resolve())
    assert result.video_path == str(video_path.resolve())


def test_invalid_video_does_not_open_browser(tmp_path):
    browser = FakeBrowser()

    with pytest.raises(RuntimeError):
        YouTubeStudioUploadPreparer(browser=browser).prepare_upload(
            str(tmp_path / "missing.mp4")
        )

    assert browser.actions == []


def test_login_required_returns_result_without_upload(tmp_path):
    browser = FakeBrowser(logged_in=False)
    video_path = _video(tmp_path)

    result = YouTubeStudioUploadPreparer(browser=browser).prepare_upload(str(video_path))

    assert result.status == "login_required"
    assert result.logged_in is False
    assert result.upload_started is False
    assert not any(action[0] == "upload" for action in browser.actions)


def test_login_only_does_not_upload(tmp_path):
    browser = FakeBrowser()

    result = YouTubeStudioUploadPreparer(
        config=YouTubeBrowserConfig(user_data_dir=tmp_path / "profile"),
        browser=browser,
    ).login_only()

    assert result.logged_in is True
    assert browser.actions == [("open", "https://studio.youtube.com/")]


def test_keep_open_waits_for_user_without_closing(tmp_path):
    browser = FakeBrowser()
    video_path = _video(tmp_path)
    prompts = []

    YouTubeStudioUploadPreparer(browser=browser).prepare_upload(
        str(video_path),
        keep_open=True,
        input_func=lambda prompt: prompts.append(prompt),
    )

    assert prompts
    assert browser.closed is False


def test_login_only_keep_open_rechecks_after_manual_login(tmp_path):
    class LoginChangingBrowser(FakeBrowser):
        def __init__(self):
            super().__init__(logged_in=False)

        def is_visible(self, selector):
            return selector in self.visible and "accounts.google.com" not in self.current_url

    browser = LoginChangingBrowser()
    prompts = []

    result = YouTubeStudioUploadPreparer(browser=browser).login_only(
        keep_open=True,
        input_func=lambda prompt: (
            prompts.append(prompt),
            setattr(browser, "current_url", "https://studio.youtube.com/"),
        ),
    )

    assert prompts
    assert result.logged_in is True
