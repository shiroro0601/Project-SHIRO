import os

import pytest

from main_v17_youtube_oauth_setup import run_youtube_oauth_setup
from company.youtube.config import YouTubeOAuthConfig


@pytest.mark.skipif(
    os.environ.get("PROJECT_SHIRO_RUN_YOUTUBE_OAUTH_SMOKE") != "1",
    reason="Requires real Google OAuth browser authentication.",
)
def test_youtube_oauth_smoke():
    result = run_youtube_oauth_setup(YouTubeOAuthConfig.from_env())

    assert result["status"] == "authenticated"
    assert result["client"] is not None
