import pytest

import main_v22_youtube_private_save_verify as cli
from company.youtube.studio_upload import YouTubePrivateSaveVerificationResult


class FakeVerifier:
    def __init__(self, status="verified_private"):
        self.status = status
        self.titles = []

    def verify(self, title):
        self.titles.append(title)
        return YouTubePrivateSaveVerificationResult(
            status=self.status,
            found=self.status != "not_found",
            title=title,
            title_matched=self.status == "verified_private",
            privacy_status="private" if self.status == "verified_private" else "",
            private_confirmed=self.status == "verified_private",
            duplicate_count=1 if self.status == "verified_private" else 0,
            video_url="https://www.youtube.com/watch?v=abc123"
            if self.status == "verified_private"
            else "",
            studio_url="https://studio.youtube.com/video/abc123/edit"
            if self.status == "verified_private"
            else "",
            error="" if self.status == "verified_private" else self.status,
            matched_title=title if self.status == "verified_private" else "",
            match_type="exact" if self.status == "verified_private" else "",
            video_id="abc123" if self.status == "verified_private" else "",
            content_type="video" if self.status == "verified_private" else "unknown",
            checked_locations=("video", "short", "live", "draft"),
        )


def test_verify_cli_requires_title():
    with pytest.raises(SystemExit):
        cli.parse_args([])


def test_verify_cli_does_not_accept_write_options():
    for option in ("--video", "--confirm-private-save", "--publish", "--visibility", "--delete", "--save"):
        with pytest.raises(SystemExit):
            cli.parse_args(["--title", "Title", option, "value"])


def test_verify_cli_accepts_reliability_options():
    args = cli.parse_args(
        [
            "--title",
            "Title",
            "--timeout-seconds",
            "12",
            "--poll-interval-seconds",
            "3",
            "--max-items",
            "25",
            "--no-wait",
        ]
    )

    assert args.timeout_seconds == 12
    assert args.poll_interval_seconds == 3
    assert args.max_items == 25
    assert args.no_wait is True


def test_run_verify_returns_read_only_result():
    verifier = FakeVerifier()
    args = cli.parse_args(["--title", "Project SHIRO Private Smoke Test"])

    result = cli.run_verify(args, verifier=verifier)

    assert verifier.titles == ["Project SHIRO Private Smoke Test"]
    assert result["status"] == "verified_private"
    assert result["private_confirmed"] is True
    assert result["duplicate_count"] == 1
    assert result["video_id"] == "abc123"
    assert result["content_type"] == "video"


def test_main_returns_zero_for_verified_private(capsys):
    code = cli.main(["--title", "Title"], verifier=FakeVerifier())

    captured = capsys.readouterr()
    assert code == 0
    assert "status: verified_private" in captured.out
    assert "private_confirmed: True" in captured.out


def test_main_returns_nonzero_for_not_found(capsys):
    code = cli.main(["--title", "Title"], verifier=FakeVerifier(status="not_found"))

    captured = capsys.readouterr()
    assert code == 1
    assert "status: not_found" in captured.out


def test_import_has_no_side_effects():
    assert hasattr(cli, "main")
