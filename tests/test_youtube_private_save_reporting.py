from company.reports.run_report import RunReport, build_run_report
from company.reports.run_report_memory_adapter import RunReportMemoryAdapter


def test_run_report_defaults_keep_old_reports_compatible():
    report = RunReport(
        topic="猫の意外な雑学",
        created_at="2026-07-13T00:00:00",
        media_mode="placeholder",
        status="completed",
        research_result="research",
        script_result="script",
        review_result="review",
        script_title="title",
        scenes=[],
        assets=[],
        image_path="image.png",
        voice_path="voice.wav",
        video_path="video.mp4",
        scene_video_path=None,
    )

    assert report.youtube_save_status == ""
    assert report.youtube_privacy_status == ""
    assert report.youtube_saved is False
    assert report.youtube_published is False
    assert report.youtube_video_url == ""
    assert report.youtube_studio_url == ""
    assert report.youtube_save_error == ""
    assert report.youtube_verification_status == ""
    assert report.youtube_private_confirmed is False
    assert report.youtube_duplicate_count == 0
    assert report.youtube_video_id == ""
    assert report.youtube_content_type == ""
    assert report.youtube_verification_error == ""


def test_build_run_report_copies_youtube_private_save_fields():
    report = build_run_report(
        topic="猫の意外な雑学",
        media_mode="placeholder",
        result={
            "review_result": "review",
            "youtube_save_status": "private_saved",
            "youtube_privacy_status": "private",
            "youtube_saved": True,
            "youtube_published": False,
            "youtube_video_url": "https://youtu.be/private-video",
            "youtube_studio_url": "https://studio.youtube.com/video/private/edit",
            "youtube_save_error": "",
            "youtube_verification_status": "verified_private",
            "youtube_private_confirmed": True,
            "youtube_duplicate_count": 1,
            "youtube_video_id": "abc123",
            "youtube_content_type": "video",
            "youtube_verification_error": "",
        },
    )

    assert report.youtube_save_status == "private_saved"
    assert report.youtube_privacy_status == "private"
    assert report.youtube_saved is True
    assert report.youtube_published is False
    assert report.youtube_video_url == "https://youtu.be/private-video"
    assert report.youtube_studio_url == "https://studio.youtube.com/video/private/edit"
    assert report.youtube_verification_status == "verified_private"
    assert report.youtube_private_confirmed is True
    assert report.youtube_duplicate_count == 1
    assert report.youtube_video_id == "abc123"
    assert report.youtube_content_type == "video"


def test_memory_adapter_adds_youtube_private_save_fields_and_summary():
    report = RunReport(
        topic="猫の意外な雑学",
        created_at="2026-07-13T00:00:00",
        media_mode="placeholder",
        status="completed",
        research_result="research",
        script_result="script",
        review_result="review",
        script_title="title",
        scenes=[],
        assets=[],
        image_path="image.png",
        voice_path="voice.wav",
        video_path="video.mp4",
        scene_video_path=None,
        youtube_save_status="private_saved",
        youtube_privacy_status="private",
        youtube_saved=True,
        youtube_published=False,
        youtube_video_url="https://youtu.be/private-video",
        youtube_studio_url="https://studio.youtube.com/video/private/edit",
        youtube_verification_status="verified_private",
        youtube_private_confirmed=True,
        youtube_duplicate_count=1,
        youtube_video_id="abc123",
        youtube_content_type="video",
    )

    record = RunReportMemoryAdapter().to_memory_record(report)

    assert record["youtube_save_status"] == "private_saved"
    assert record["youtube_privacy_status"] == "private"
    assert record["youtube_saved"] is True
    assert record["youtube_published"] is False
    assert record["youtube_video_url"] == "https://youtu.be/private-video"
    assert record["youtube_studio_url"] == "https://studio.youtube.com/video/private/edit"
    assert record["youtube_verification_status"] == "verified_private"
    assert record["youtube_private_confirmed"] is True
    assert record["youtube_duplicate_count"] == 1
    assert record["youtube_video_id"] == "abc123"
    assert record["youtube_content_type"] == "video"
    assert "YouTubeへprivateで保存済み" in record["summary"]
    assert "YouTube非公開保存をRead-only検証済み" in record["summary"]
