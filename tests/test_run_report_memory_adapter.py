from company.reports.run_report import RunReport
from company.reports.run_report_memory_adapter import RunReportMemoryAdapter


def make_report() -> RunReport:
    return RunReport(
        topic="猫の意外な雑学",
        created_at="2026-07-09T10:00:00",
        media_mode="placeholder",
        status="completed",
        research_result="research",
        script_result="script",
        review_result="review",
        script_title="猫タイトル",
        scenes=[
            {"index": 1, "narration": "scene 1"},
            {"index": 2, "narration": "scene 2"},
        ],
        assets=[
            {"scene_index": 1, "image_path": "image_1.png"},
            {"scene_index": 2, "image_path": "image_2.png"},
        ],
        image_path="image_1.png",
        voice_path="voice_1.wav",
        video_path="final_video.mp4",
        scene_video_path="final_video.mp4",
        quality_feedback={
            "evaluation": "分かりやすい台本です。",
            "improvement_points": "冒頭の引きを強くする",
            "decision": "合格",
            "score": 1.0,
        },
    )


def test_run_report_memory_adapter_creates_memory_record():
    record = RunReportMemoryAdapter().to_memory_record(make_report())

    assert record["type"] == "real_ai_company_run"
    assert record["topic"] == "猫の意外な雑学"
    assert record["media_mode"] == "placeholder"
    assert record["status"] == "completed"
    assert record["script_title"] == "猫タイトル"
    assert record["video_path"] == "final_video.mp4"


def test_run_report_memory_adapter_counts_scenes_and_assets():
    record = RunReportMemoryAdapter().to_memory_record(make_report())

    assert record["scene_count"] == 2
    assert record["asset_count"] == 2


def test_run_report_memory_adapter_summary_contains_topic_and_media_mode():
    record = RunReportMemoryAdapter().to_memory_record(make_report())

    assert "猫の意外な雑学" in record["summary"]
    assert "placeholder mode" in record["summary"]
    assert "2 scenes / 2 assets" in record["summary"]
    assert "品質判定: 合格" in record["summary"]


def test_run_report_memory_adapter_adds_quality_fields():
    record = RunReportMemoryAdapter().to_memory_record(make_report())

    assert record["quality_decision"] == "合格"
    assert record["quality_score"] == 1.0
    assert record["improvement_points"] == "冒頭の引きを強くする"
