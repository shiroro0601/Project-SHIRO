import os

import pytest

from main_v16_topic_to_real_video import run_topic_to_real_video


@pytest.mark.skipif(
    os.environ.get("PROJECT_SHIRO_RUN_REAL_SERVICES") != "1",
    reason="Requires local Ollama, Stable Diffusion WebUI API, and VOICEVOX.",
)
def test_topic_to_real_video_smoke():
    result = run_topic_to_real_video("猫の意外な雑学")

    assert result["video_validation"]["exists"] is True
    assert result["video_validation"]["size_bytes"] > 0
