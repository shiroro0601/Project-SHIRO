import pytest

import main_v24_youtube_controlled_private_smoke as cli
from company.youtube.studio_upload import YouTubeControlledPrivateSaveResult


class FakeControlledRunner:
    def __init__(self, status="verified_private"):
        self.calls = []
        self.status = status

    def run(
        self,
        video_path,
        metadata,
        smoke_id,
        expected_channel_name,
        confirm_private_save,
        keep_open=False,
    ):
        self.calls.append(
            (
                video_path,
                metadata,
                smoke_id,
                expected_channel_name,
                confirm_private_save,
                keep_open,
            )
        )
        return YouTubeControlledPrivateSaveResult(
            status=self.status,
            smoke_id=smoke_id,
            title=f"Project SHIRO Private Smoke {smoke_id}",
            channel_identity_confirmed=True,
            private_selected=True,
            save_clicked=self.status != "duplicate_save_blocked",
            saved=self.status == "verified_private",
            published=False,
            privacy_status="private",
            verification_status="verified_private" if self.status == "verified_private" else "",
            found=self.status == "verified_private",
            private_confirmed=self.status == "verified_private",
            duplicate_count=1 if self.status == "verified_private" else 0,
            video_id="abc123" if self.status == "verified_private" else "",
            video_url="https://www.youtube.com/watch?v=abc123"
            if self.status == "verified_private"
            else "",
            studio_url="https://studio.youtube.com/video/abc123/edit"
            if self.status == "verified_private"
            else "",
            content_type="video",
            error="" if self.status == "verified_private" else self.status,
        )


def required_args():
    return [
        "--expected-channel-name",
        "恋愛らぼっ！",
        "--video",
        "video.mp4",
        "--smoke-id",
        "20260713-001",
        "--description",
        "Project SHIROのPrivate保存確認動画です。",
        "--tag",
        "ProjectSHIRO",
        "--not-made-for-kids",
        "--confirm-private-save",
    ]


def test_cli_requires_expected_channel_name():
    with pytest.raises(SystemExit):
        cli.parse_args(
            [
                "--video",
                "video.mp4",
                "--smoke-id",
                "20260713-001",
                "--not-made-for-kids",
                "--confirm-private-save",
            ]
        )


def test_cli_requires_smoke_id():
    args = required_args()
    args.remove("--smoke-id")
    args.remove("20260713-001")

    with pytest.raises(SystemExit):
        cli.parse_args(args)


def test_cli_requires_confirm_flag():
    args = required_args()
    args.remove("--confirm-private-save")

    with pytest.raises(SystemExit):
        cli.parse_args(args)


def test_cli_success_returns_zero_and_passes_metadata(capsys):
    runner = FakeControlledRunner()

    exit_code = cli.main(required_args(), runner=runner)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert runner.calls
    assert runner.calls[0][2] == "20260713-001"
    assert runner.calls[0][3] == "恋愛らぼっ！"
    assert runner.calls[0][4] is True
    assert runner.calls[0][1].description == "Project SHIROのPrivate保存確認動画です。"
    assert runner.calls[0][1].tags == ("ProjectSHIRO",)
    assert "status: verified_private" in output


def test_cli_duplicate_smoke_id_returns_nonzero(capsys):
    runner = FakeControlledRunner(status="duplicate_save_blocked")

    exit_code = cli.main(required_args(), runner=runner)

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "duplicate_save_blocked" in output


def test_cli_import_does_not_run_main():
    assert hasattr(cli, "main")
