import os

import pytest

from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeBrowserConfig,
    YouTubeCDPConfig,
    YouTubeMetadataPreparer,
    YouTubeStudioUploadPreparer,
    YouTubeVideoMetadata,
)


@pytest.mark.skipif(
    os.environ.get("PROJECT_SHIRO_RUN_YOUTUBE_METADATA_SMOKE") != "1",
    reason="Requires a user-launched Chrome CDP session and YouTube Studio login.",
)
def test_youtube_metadata_prepare_smoke():
    endpoint = os.environ.get(
        "PROJECT_SHIRO_YOUTUBE_STUDIO_CDP_ENDPOINT",
        "http://127.0.0.1:9222",
    )
    video_path = os.environ.get(
        "PROJECT_SHIRO_YOUTUBE_STUDIO_SMOKE_VIDEO",
        "outputs/real_video/videos/final_video.mp4",
    )
    browser = PlaywrightCDPBrowserController(
        config=YouTubeCDPConfig(endpoint_url=endpoint)
    ).start()
    upload_preparer = YouTubeStudioUploadPreparer(
        config=YouTubeBrowserConfig(),
        browser=browser,
    )
    metadata = YouTubeVideoMetadata(
        title="猫の意外な雑学",
        description="猫に関する意外な雑学を紹介します。\nぜひ最後までご覧ください。",
        made_for_kids=False,
        tags=("猫", "雑学"),
    )

    result = YouTubeMetadataPreparer(upload_preparer).prepare_metadata(
        video_path,
        metadata,
        keep_open=True,
    )

    assert result.status == "metadata_prepared"
    assert result.title_applied is True
    assert result.description_applied is True
    assert result.audience_applied is True
    assert result.tags_applied is True
    assert result.saved is False
    assert result.published is False
