from company.runtime.project_shiro_youtube_orchestrator import (
    ProjectShiroStopPoint,
    ProjectShiroYouTubeRunResult,
)


def test_result_defaults_are_private_safe():
    result = ProjectShiroYouTubeRunResult(
        status="stopped_before_save",
        topic="猫の意外な雑学",
    )

    assert result.saved is False
    assert result.published is False
    assert result.stop_point == ProjectShiroStopPoint.BEFORE_SAVE


def test_result_to_dict_preserves_urls_and_checkpoints():
    result = ProjectShiroYouTubeRunResult(
        status="private_verified",
        topic="猫の意外な雑学",
        video_id="abc123",
        video_url="https://youtu.be/abc123",
        studio_url="https://studio.youtube.com/video/abc123/edit",
        checked_locations=("video", "draft"),
    )
    result.checkpoints.append({"name": "verified_private"})

    data = result.to_dict()

    assert data["video_id"] == "abc123"
    assert data["video_url"] == "https://youtu.be/abc123"
    assert data["studio_url"] == "https://studio.youtube.com/video/abc123/edit"
    assert data["checked_locations"] == ("video", "draft")
    assert data["checkpoints"] == [{"name": "verified_private"}]
