import os

import pytest

from company.youtube.studio_upload import (
    PlaywrightCDPBrowserController,
    YouTubeBrowserConfig,
    YouTubeCDPConfig,
    YouTubeMetadataPreparer,
    YouTubePrivateSaveConfirmer,
    YouTubePrivateSavePolicy,
    YouTubeStudioUploadPreparer,
    YouTubeVideoMetadata,
)


@pytest.mark.skipif(
    os.getenv("PROJECT_SHIRO_RUN_YOUTUBE_PRIVATE_SAVE_SMOKE") != "1",
    reason="Requires explicit real YouTube private save confirmation.",
)
def test_youtube_private_save_smoke():
    endpoint = os.getenv("PROJECT_SHIRO_YOUTUBE_CDP_ENDPOINT", "http://127.0.0.1:9222")
    video = os.getenv(
        "PROJECT_SHIRO_YOUTUBE_PRIVATE_SAVE_VIDEO",
        "outputs/real_video/videos/final_video.mp4",
    )
    metadata = YouTubeVideoMetadata(
        title=os.getenv("PROJECT_SHIRO_YOUTUBE_PRIVATE_SAVE_TITLE", "Project SHIRO Private Smoke Test"),
        description=os.getenv(
            "PROJECT_SHIRO_YOUTUBE_PRIVATE_SAVE_DESCRIPTION",
            "Project SHIROの非公開投稿確認です。",
        ),
        made_for_kids=False,
        tags=("ProjectSHIRO",),
    )
    browser = PlaywrightCDPBrowserController(
        config=YouTubeCDPConfig(endpoint_url=endpoint)
    ).start()
    upload_preparer = YouTubeStudioUploadPreparer(
        config=YouTubeBrowserConfig(),
        browser=browser,
    )
    metadata_preparer = YouTubeMetadataPreparer(upload_preparer)

    result = YouTubePrivateSaveConfirmer(metadata_preparer).save_private(
        video,
        metadata,
        policy=YouTubePrivateSavePolicy(confirm_private_save=True),
        keep_open=True,
    )

    assert result.status == "private_saved"
    assert result.private_selected is True
    assert result.save_clicked is True
    assert result.saved is True
    assert result.published is False
    assert result.privacy_status == "private"
