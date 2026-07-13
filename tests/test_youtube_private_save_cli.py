import pytest

import main_v21_youtube_private_save as cli
from company.youtube.studio_upload import YouTubePrivateSaveResult


class FakePrivateSaveConfirmer:
    def __init__(self, status="private_saved"):
        self.status = status
        self.calls = []

    def save_private(self, video_path, metadata, policy, keep_open=False):
        self.calls.append(
            {
                "video_path": video_path,
                "metadata": metadata,
                "policy": policy,
                "keep_open": keep_open,
            }
        )
        return YouTubePrivateSaveResult(
            status=self.status,
            video_path=video_path,
            title=metadata.title,
            privacy_status="private",
            private_selected=self.status == "private_saved",
            save_clicked=self.status == "private_saved",
            saved=self.status == "private_saved",
            published=False,
            video_url="https://youtu.be/private-video"
            if self.status == "private_saved"
            else "",
            studio_url="https://studio.youtube.com/video/private/edit"
            if self.status == "private_saved"
            else "",
            error="" if self.status == "private_saved" else self.status,
        )


def args(*extra):
    return [
        "--video",
        "video.mp4",
        "--title",
        "猫の意外な雑学",
        "--description",
        "説明",
        "--tag",
        "猫",
        "--not-made-for-kids",
        *extra,
    ]


def test_parse_args_requires_audience():
    with pytest.raises(SystemExit):
        cli.parse_args(["--video", "video.mp4", "--title", "title"])


def test_parse_args_does_not_define_public_or_unlisted_options():
    with pytest.raises(SystemExit):
        cli.parse_args([*args("--confirm-private-save"), "--public"])
    with pytest.raises(SystemExit):
        cli.parse_args([*args("--confirm-private-save"), "--unlisted"])


def test_run_without_confirm_returns_confirmation_required():
    confirmer = FakePrivateSaveConfirmer(status="confirmation_required")
    parsed = cli.parse_args(args())

    result = cli.run_private_save(parsed, private_save_confirmer=confirmer)

    assert result["status"] == "confirmation_required"
    assert confirmer.calls[0]["policy"].confirm_private_save is False
    assert result["saved"] is False
    assert result["published"] is False


def test_run_with_confirm_enables_private_save():
    confirmer = FakePrivateSaveConfirmer()
    parsed = cli.parse_args(args("--confirm-private-save", "--keep-open"))

    result = cli.run_private_save(parsed, private_save_confirmer=confirmer)

    assert result["status"] == "private_saved"
    assert confirmer.calls[0]["policy"].confirm_private_save is True
    assert confirmer.calls[0]["keep_open"] is True
    assert result["privacy_status"] == "private"


def test_main_returns_zero_on_private_saved(capsys):
    code = cli.main(args("--confirm-private-save"), private_save_confirmer=FakePrivateSaveConfirmer())

    captured = capsys.readouterr()
    assert code == 0
    assert "status: private_saved" in captured.out
    assert "published: False" in captured.out


def test_main_returns_nonzero_on_failure(capsys):
    code = cli.main(
        args("--confirm-private-save"),
        private_save_confirmer=FakePrivateSaveConfirmer(status="private_selection_failed"),
    )

    captured = capsys.readouterr()
    assert code == 1
    assert "status: private_selection_failed" in captured.out


def test_import_has_no_side_effects():
    assert hasattr(cli, "main")
