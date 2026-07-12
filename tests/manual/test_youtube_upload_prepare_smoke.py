import os

import pytest

from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeCDPConfig,
    YouTubeStudioUploadPreparer,
)


@pytest.mark.skipif(
    os.environ.get("PROJECT_SHIRO_RUN_YOUTUBE_STUDIO_SMOKE") != "1",
    reason="Requires real Playwright browser and YouTube Studio login.",
)
def test_youtube_upload_prepare_smoke():
    video_path = os.environ.get(
        "PROJECT_SHIRO_YOUTUBE_STUDIO_SMOKE_VIDEO",
        "outputs/real_video/videos/final_video.mp4",
    )
    endpoint = os.environ.get(
        "PROJECT_SHIRO_YOUTUBE_STUDIO_CDP_ENDPOINT",
        "http://127.0.0.1:9222",
    )
    browser = PlaywrightCDPBrowserController(
        config=YouTubeCDPConfig(endpoint_url=endpoint)
    ).start()

    result = YouTubeStudioUploadPreparer(browser=browser).prepare_upload(
        video_path,
        keep_open=True,
    )

    assert result.status == "prepared"
    assert result.upload_started is True
    assert result.saved is False
    assert result.published is False
