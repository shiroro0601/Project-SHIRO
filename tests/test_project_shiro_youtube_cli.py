from types import SimpleNamespace

import pytest

import main_v30_project_shiro as cli
from company.runtime.project_shiro_youtube_orchestrator import ProjectShiroStopPoint


class FakeOrchestrator:
    def __init__(self, status="stopped_before_save"):
        self.status = status
        self.config = None

    def run(self, config):
        self.config = config
        return SimpleNamespace(
            status=self.status,
            topic=config.topic,
            video_path="outputs/real_video/videos/final_video.mp4",
            video_size=123,
            upload_status="prepared",
            metadata_status="metadata_prepared",
            save_status="",
            verification_status="",
            channel_identity_confirmed=True,
            title=config.title or config.topic,
            private_selected=False,
            save_clicked=False,
            saved=False,
            published=False,
            privacy_status="",
            video_id="",
            video_url="",
            studio_url="",
            stop_point=config.stop_point,
            failure_stage="",
            run_report_path="report.json",
            error="",
        )


def base_args():
    return [
        "--topic",
        "猫の意外な雑学",
        "--not-made-for-kids",
    ]


def test_parse_requires_topic():
    with pytest.raises(SystemExit):
        cli.parse_args(["--not-made-for-kids"])


def test_parse_requires_audience():
    with pytest.raises(SystemExit):
        cli.parse_args(["--topic", "猫"])


def test_default_stop_point_is_before_save():
    args = cli.parse_args(base_args())

    assert cli.stop_point_from_args(args) == ProjectShiroStopPoint.BEFORE_SAVE


def test_confirm_private_save_defaults_to_no_stop_point():
    args = cli.parse_args(
        base_args()
        + [
            "--confirm-private-save",
            "--expected-channel-name",
            "恋愛らぼっ‼",
            "--smoke-id",
            "unique",
        ]
    )

    assert cli.stop_point_from_args(args) == ProjectShiroStopPoint.NONE


def test_explicit_stop_flag_wins_over_confirm():
    args = cli.parse_args(
        base_args()
        + [
            "--confirm-private-save",
            "--expected-channel-name",
            "恋愛らぼっ‼",
            "--smoke-id",
            "unique",
            "--stop-before-save",
        ]
    )

    assert cli.stop_point_from_args(args) == ProjectShiroStopPoint.BEFORE_SAVE


def test_main_returns_zero_for_safe_stop(capsys):
    fake = FakeOrchestrator()

    exit_code = cli.main(base_args(), orchestrator=fake)

    assert exit_code == 0
    assert fake.config.topic == "猫の意外な雑学"
    assert fake.config.made_for_kids is False
    captured = capsys.readouterr()
    assert "status: stopped_before_save" in captured.out
    assert "published: False" in captured.out


def test_existing_video_arg_is_preserved():
    args = cli.parse_args(base_args() + ["--existing-video", "final_video.mp4"])
    config = cli.build_config(args)

    assert config.existing_video_path == "final_video.mp4"


def test_main_returns_nonzero_for_failure():
    fake = FakeOrchestrator(status="cdp_connection_failed")

    assert cli.main(base_args(), orchestrator=fake) == 1


def test_build_config_rejects_confirm_without_smoke_id():
    args = cli.parse_args(
        base_args()
        + [
            "--confirm-private-save",
            "--expected-channel-name",
            "恋愛らぼっ‼",
        ]
    )

    with pytest.raises(ValueError):
        cli.build_config(args)
