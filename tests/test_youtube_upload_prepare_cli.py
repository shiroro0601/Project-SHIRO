import importlib
from pathlib import Path

import main_v18_youtube_studio_upload_prepare as cli


class FakePreparer:
    def __init__(self, result):
        self.result = result
        self.login_called = False
        self.prepare_called = False

    def login_only(self, keep_open=False):
        self.login_called = True
        self.keep_open = keep_open
        return self.result

    def prepare_upload(self, video_path, keep_open=False):
        self.prepare_called = True
        self.video_path = video_path
        self.keep_open = keep_open
        return self.result


class FakeLoginResult:
    status = "logged_in"
    logged_in = True
    current_url = "https://studio.youtube.com/"
    reason = ""


class FakeUploadResult:
    status = "prepared"
    video_path = "video.mp4"
    filename = "video.mp4"
    upload_started = True
    details_visible = True
    logged_in = True
    current_url = "https://studio.youtube.com/"
    saved = False
    published = False
    error = ""


def test_cli_login_only_does_not_upload(capsys):
    preparer = FakePreparer(FakeLoginResult())

    exit_code = cli.main(["--login-only"], preparer=preparer)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert preparer.login_called is True
    assert preparer.prepare_called is False
    assert "upload_started: False" in output


def test_cli_prepare_upload_success(capsys):
    preparer = FakePreparer(FakeUploadResult())

    exit_code = cli.main(["--video", "video.mp4", "--keep-open"], preparer=preparer)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert preparer.prepare_called is True
    assert preparer.video_path == "video.mp4"
    assert preparer.keep_open is True
    assert "saved: False" in output
    assert "published: False" in output


def test_cli_build_config_uses_required_absolute_default_profile():
    args = cli.parse_args(["--login-only"])

    config = cli.build_config(args)

    expected = (
        Path(
            "C:/Users/Koshi/Documents/Codex/2026-07-01/"
            "project-shiro-version1-0-pytest-project/work/"
            "Project-SHIRO-workflow-loop/outputs/browser_profiles/youtube"
        )
        .resolve()
    )
    assert config.user_data_dir == expected


def test_cli_accepts_browser_channel_chrome():
    args = cli.parse_args(["--login-only", "--browser-channel", "chrome"])

    config = cli.build_config(args)

    assert config.browser_channel == "chrome"


def test_cli_accepts_cdp_connection_mode():
    args = cli.parse_args(
        [
            "--login-only",
            "--connection-mode",
            "cdp",
            "--cdp-endpoint",
            "http://127.0.0.1:9222",
        ]
    )

    assert args.connection_mode == "cdp"
    assert args.cdp_endpoint == "http://127.0.0.1:9222"
    assert cli.build_cdp_config(args).endpoint_url == "http://127.0.0.1:9222"


def test_cli_prints_cdp_chrome_command(capsys):
    exit_code = cli.main(["--print-cdp-chrome-command"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "--remote-debugging-address=127.0.0.1" in output
    assert "--remote-debugging-port=9222" in output
    assert "outputs" in output
    assert "youtube_cdp" in output
    assert "https://studio.youtube.com/" in output


def test_cli_build_preparer_uses_cdp_controller(monkeypatch):
    created = {}

    class FakeCDPController:
        def __init__(self, config):
            created["endpoint_url"] = config.endpoint_url
            created["started"] = False

        def start(self):
            created["started"] = True
            return self

    monkeypatch.setattr(cli, "PlaywrightCDPBrowserController", FakeCDPController)
    args = cli.parse_args(
        [
            "--login-only",
            "--connection-mode",
            "cdp",
            "--cdp-endpoint",
            "http://localhost:9222",
        ]
    )

    preparer = cli.build_preparer(args)

    assert created == {
        "endpoint_url": "http://localhost:9222",
        "started": True,
    }
    assert preparer.browser.__class__ is FakeCDPController


def test_cli_profile_dir_override_is_preserved(tmp_path):
    profile_dir = tmp_path / "profile"
    args = cli.parse_args(["--login-only", "--profile-dir", str(profile_dir)])

    config = cli.build_config(args)

    assert config.user_data_dir == profile_dir


def test_cli_requires_video_unless_login_only(capsys):
    exit_code = cli.main([], preparer=FakePreparer(FakeUploadResult()))

    assert exit_code == 1
    assert "failed" in capsys.readouterr().out


def test_cli_import_has_no_side_effects(monkeypatch):
    called = {"main": False}
    monkeypatch.setattr(cli, "main", lambda *args, **kwargs: called.__setitem__("main", True))

    importlib.reload(cli)

    assert called["main"] is False
