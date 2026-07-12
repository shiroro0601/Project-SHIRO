import importlib

import pytest

import main_v20_youtube_studio_metadata_prepare as cli
from company.youtube.studio_upload import YouTubeMetadataPreparationResult


class FakeMetadataPreparer:
    def __init__(self, status="metadata_prepared"):
        self.status = status
        self.calls = []

    def prepare_metadata(self, video_path, metadata, keep_open=False):
        self.calls.append(
            {
                "video_path": video_path,
                "metadata": metadata,
                "keep_open": keep_open,
            }
        )
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
            error="" if self.status == "metadata_prepared" else "failed",
        )


def test_cli_accepts_metadata_arguments():
    args = cli.parse_args(
        [
            "--video",
            "video.mp4",
            "--title",
            "猫の意外な雑学",
            "--description",
            "説明",
            "--tag",
            "猫",
            "--tag",
            "雑学",
            "--not-made-for-kids",
        ]
    )
    metadata = cli.build_metadata(args)

    assert metadata.title == "猫の意外な雑学"
    assert metadata.description == "説明"
    assert metadata.tags == ("猫", "雑学")
    assert metadata.made_for_kids is False


def test_cli_accepts_made_for_kids():
    args = cli.parse_args(
        [
            "--video",
            "video.mp4",
            "--title",
            "猫",
            "--made-for-kids",
        ]
    )

    assert cli.build_metadata(args).made_for_kids is True


def test_cli_rejects_missing_audience():
    with pytest.raises(SystemExit):
        cli.parse_args(["--video", "video.mp4", "--title", "猫"])


def test_cli_rejects_conflicting_audience():
    with pytest.raises(SystemExit):
        cli.parse_args(
            [
                "--video",
                "video.mp4",
                "--title",
                "猫",
                "--made-for-kids",
                "--not-made-for-kids",
            ]
        )


def test_cli_success_returns_zero(capsys):
    preparer = FakeMetadataPreparer()

    code = cli.main(
        [
            "--video",
            "video.mp4",
            "--title",
            "猫",
            "--not-made-for-kids",
        ],
        metadata_preparer=preparer,
    )

    output = capsys.readouterr().out
    assert code == 0
    assert preparer.calls[0]["metadata"].title == "猫"
    assert "status: metadata_prepared" in output
    assert "saved: False" in output
    assert "published: False" in output


def test_cli_failure_returns_non_zero(capsys):
    code = cli.main(
        [
            "--video",
            "video.mp4",
            "--title",
            "猫",
            "--not-made-for-kids",
        ],
        metadata_preparer=FakeMetadataPreparer(status="title_apply_failed"),
    )

    assert code == 1
    assert "error: failed" in capsys.readouterr().out


def test_cli_import_has_no_side_effects(monkeypatch):
    called = {"main": False}
    monkeypatch.setattr(cli, "main", lambda *args, **kwargs: called.__setitem__("main", True))

    importlib.reload(cli)

    assert called["main"] is False
