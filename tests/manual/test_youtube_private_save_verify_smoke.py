import os

import pytest

from company.youtube.studio_upload import (
    YouTubeCDPConfig,
    YouTubePrivateSaveVerifier,
)


@pytest.mark.skipif(
    os.getenv("PROJECT_SHIRO_RUN_YOUTUBE_PRIVATE_SAVE_VERIFY_SMOKE") != "1",
    reason="Requires a user-launched Chrome CDP session and YouTube Studio login.",
)
def test_youtube_private_save_verify_smoke():
    endpoint = os.getenv("PROJECT_SHIRO_YOUTUBE_CDP_ENDPOINT", "http://127.0.0.1:9222")
    title = os.getenv(
        "PROJECT_SHIRO_YOUTUBE_PRIVATE_SAVE_TITLE",
        "Project SHIRO Private Smoke Test",
    )

    result = YouTubePrivateSaveVerifier(
        config=YouTubeCDPConfig(endpoint_url=endpoint)
    ).verify(title)

    assert result.status == "verified_private"
    assert result.found is True
    assert result.title_matched is True
    assert result.private_confirmed is True
    assert result.privacy_status == "private"
    assert result.duplicate_count == 1
