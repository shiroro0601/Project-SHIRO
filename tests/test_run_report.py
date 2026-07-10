import json
from pathlib import Path

from company.artifacts.scene_artifact import SceneArtifact
from company.artifacts.scene_asset import SceneAsset
from company.artifacts.script_artifact import ScriptArtifact
from company.reports.run_report import (
    RunReport,
    RunReportWriter,
    build_run_report,
)


def test_run_report_can_be_created():
    report = RunReport(
        topic="猫の意外な雑学",
        created_at="2026-07-09T00:00:00",
        media_mode="placeholder",
        status="completed",
        research_result="research",
        script_result="script",
        review_result="review",
        script_title="猫タイトル",
        scenes=[],
        assets=[],
        image_path="image.png",
        voice_path="voice.wav",
        video_path="video.mp4",
        scene_video_path=None,
    )

    assert report.topic == "猫の意外な雑学"
    assert report.status == "completed"
    assert report.quality_feedback == {}
    assert report.quality_retry_count == 0
    assert report.quality_retry_history == []


def test_run_report_writer_saves_json_with_japanese(tmp_path):
    report = RunReport(
        topic="猫の意外な雑学",
        created_at="2026-07-09T00:00:00",
        media_mode="placeholder",
        status="completed",
        research_result="猫の調査",
        script_result="猫の台本",
        review_result="合格",
        script_title="猫タイトル",
        scenes=[],
        assets=[],
        image_path="image.png",
        voice_path="voice.wav",
        video_path="video.mp4",
        scene_video_path="video.mp4",
    )
    writer = RunReportWriter(output_dir=str(tmp_path))

    output_path = writer.write(report)

    saved_text = Path(output_path).read_text(encoding="utf-8")
    assert "猫の意外な雑学" in saved_text
    assert "\\u732b" not in saved_text
    data = json.loads(saved_text)
    assert data["topic"] == "猫の意外な雑学"
    assert data["scene_video_path"] == "video.mp4"
    assert data["quality_feedback"] == {}


def test_build_run_report_converts_result_dict_to_report():
    script_artifact = ScriptArtifact(
        title="猫タイトル",
        narration="猫ナレーション",
        image_prompts=["箱に入る猫"],
        scenes=[
            SceneArtifact(
                index=1,
                narration="猫は箱が好きです。",
                image_prompt="箱に入る猫",
                duration_seconds=3.0,
            )
        ],
        raw_text="raw",
    )
    scene_asset = SceneAsset(
        scene_index=1,
        image_path="image.png",
        voice_path="voice.wav",
        narration="猫は箱が好きです。",
        image_prompt="箱に入る猫",
        duration_seconds=3.0,
    )
    result = {
        "research_result": "research",
        "script_result": "script",
        "review_result": (
            "【評価】\n"
            "分かりやすい台本です。\n\n"
            "【改善点】\n"
            "なし\n\n"
            "【判定】\n"
            "合格"
        ),
        "script_artifact": script_artifact,
        "scene_assets": [scene_asset],
        "image_path": "image.png",
        "voice_path": "voice.wav",
        "video_path": "video.mp4",
        "scene_video_path": "scene_video.mp4",
        "quality_retry_count": 1,
        "quality_retry_history": [
            {
                "attempt": 0,
                "decision": "修正必要",
                "score": 0.0,
                "improvement_points": "冒頭を改善",
            },
            {
                "attempt": 1,
                "decision": "合格",
                "score": 1.0,
                "improvement_points": "なし",
            },
        ],
    }

    report = build_run_report(
        topic="猫の意外な雑学",
        media_mode="placeholder",
        result=result,
    )

    assert report.topic == "猫の意外な雑学"
    assert report.media_mode == "placeholder"
    assert report.script_title == "猫タイトル"
    assert report.scenes == [
        {
            "index": 1,
            "narration": "猫は箱が好きです。",
            "image_prompt": "箱に入る猫",
            "duration_seconds": 3.0,
        }
    ]
    assert report.assets == [
        {
            "scene_index": 1,
            "image_path": "image.png",
            "voice_path": "voice.wav",
            "narration": "猫は箱が好きです。",
            "image_prompt": "箱に入る猫",
            "duration_seconds": 3.0,
        }
    ]
    assert report.quality_feedback == {
        "evaluation": "分かりやすい台本です。",
        "improvement_points": "なし",
        "decision": "合格",
        "score": 1.0,
    }
    assert report.quality_retry_count == 1
    assert report.quality_retry_history == [
        {
            "attempt": 0,
            "decision": "修正必要",
            "score": 0.0,
            "improvement_points": "冒頭を改善",
        },
        {
            "attempt": 1,
            "decision": "合格",
            "score": 1.0,
            "improvement_points": "なし",
        },
    ]
