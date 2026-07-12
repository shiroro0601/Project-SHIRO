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
def test_youtube_studio_login_smoke():
    endpoint = os.environ.get(
        "PROJECT_SHIRO_YOUTUBE_STUDIO_CDP_ENDPOINT",
        "http://127.0.0.1:9222",
    )
    browser = PlaywrightCDPBrowserController(
        config=YouTubeCDPConfig(endpoint_url=endpoint)
    ).start()

    result = YouTubeStudioUploadPreparer(browser=browser).login_only(keep_open=True)

    assert result.status == "logged_in"
    assert result.logged_in is True
