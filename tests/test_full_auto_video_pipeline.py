import pytest

from main_v13_full_auto_video_pipeline import (
    FullAutoVideoPipelineRunner,
    build_company,
)


def test_full_auto_video_pipeline_runs_to_draft_saved():
    runner = FullAutoVideoPipelineRunner()

    result = runner.run(
        "猫の意外な雑学"
    )

    assert result["status"] == "draft_saved"
    assert result["topic"] == "猫の意外な雑学"
    assert result["image_path"] == "outputs/images/fake_image.png"
    assert result["voice_path"] == "outputs/voices/fake_voice.wav"
    assert result["video_path"] == "outputs/videos/final_video.mp4"

    actions = [
        action[0]
        for action in result["browser_actions"]
    ]

    assert "open" in actions
    assert "upload" in actions
    assert "fill" in actions
    assert "click" in actions


def test_full_auto_video_pipeline_does_not_publish():
    runner = FullAutoVideoPipelineRunner()

    result = runner.run(
        "猫の意外な雑学"
    )

    actions_text = str(result["browser_actions"]).lower()

    assert "publish" not in actions_text


def test_full_auto_video_pipeline_rejects_empty_topic():
    runner = FullAutoVideoPipelineRunner()

    with pytest.raises(ValueError):
        runner.run("")


def test_ai_company_facade_runs_full_auto_pipeline():
    company = build_company()

    result = company.run(
        "猫の意外な雑学"
    )

    assert result["status"] == "draft_saved"
    assert result["video_path"] == "outputs/videos/final_video.mp4"