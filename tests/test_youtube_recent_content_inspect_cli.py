import pytest

import main_v23_youtube_recent_content_inspect as cli
from company.youtube.studio_upload import (
    YouTubeContentRecord,
    YouTubeRecentContentInspectionResult,
)


class FakeInspector:
    def __init__(self):
        self.target_title = None

    def inspect(self, target_title=""):
        self.target_title = target_title
        record = YouTubeContentRecord(
            title="Project SHIRO Private Smoke Test",
            normalized_title="project shiro private smoke test",
            privacy_status="private",
            processing_status="",
            content_type="video",
            video_id="abc123",
            video_url="https://www.youtube.com/watch?v=abc123",
            studio_url="https://studio.youtube.com/video/abc123/edit",
            displayed_date="2026/07/13",
            row_index=0,
            candidate_reasons=("exact_title", "private_recent"),
        )
        return YouTubeRecentContentInspectionResult(
            status="inspected",
            records=(record,),
            checked_locations=("video", "short", "live", "draft"),
            total_records=1,
            private_count=1,
            records_without_video_id=0,
            exact_matches=(record,),
            private_recent_candidates=(record,),
        )


def test_recent_content_cli_parse_args():
    args = cli.parse_args(
        [
            "--cdp-endpoint",
            "http://127.0.0.1:9222",
            "--max-items",
            "50",
            "--target-title",
            "Project SHIRO Private Smoke Test",
        ]
    )

    assert args.cdp_endpoint == "http://127.0.0.1:9222"
    assert args.max_items == 50
    assert args.target_title == "Project SHIRO Private Smoke Test"


@pytest.mark.parametrize(
    "forbidden",
    [
        "--video",
        "--save",
        "--publish",
        "--delete",
        "--visibility",
        "--confirm-private-save",
    ],
)
def test_recent_content_cli_rejects_write_or_save_options(forbidden):
    with pytest.raises(SystemExit):
        cli.parse_args([forbidden, "value"])


def test_recent_content_cli_returns_zero_and_prints_safe_summary(capsys):
    inspector = FakeInspector()

    exit_code = cli.main(
        [
            "--target-title",
            "Project SHIRO Private Smoke Test",
            "--max-items",
            "50",
        ],
        inspector=inspector,
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert inspector.target_title == "Project SHIRO Private Smoke Test"
    assert "status: inspected" in output
    assert "Project SHIRO Private Smoke Test" in output
    assert "abc123" in output
    assert "cookie" not in output.lower()


def test_recent_content_cli_import_does_not_run_main():
    assert hasattr(cli, "main")
