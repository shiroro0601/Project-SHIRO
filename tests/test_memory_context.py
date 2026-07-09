from company.memory.memory_context import MemoryContext


def test_memory_context_is_empty_when_records_are_empty():
    context = MemoryContext(records=[], prompt_text="過去の実行履歴はありません。")

    assert context.is_empty() is True


def test_memory_context_is_not_empty_when_records_exist():
    context = MemoryContext(
        records=[{"topic": "猫の意外な雑学"}],
        prompt_text="過去の実行履歴:\n1. topic: 猫の意外な雑学",
    )

    assert context.is_empty() is False


def test_memory_context_to_prompt_text_returns_prompt_text():
    context = MemoryContext(records=[], prompt_text="過去の実行履歴はありません。")

    assert context.to_prompt_text() == "過去の実行履歴はありません。"


def test_memory_context_to_prompt_text_can_include_quality_information():
    context = MemoryContext(
        records=[
            {
                "topic": "猫の意外な雑学",
                "status": "completed",
                "media_mode": "placeholder",
                "scene_count": 3,
                "asset_count": 3,
                "video_path": "outputs/videos/final_video.mp4",
                "summary": "猫動画を制作しました。品質判定: 合格。",
                "quality_decision": "合格",
                "quality_score": 1.0,
                "improvement_points": "冒頭の引きを強くする",
            }
        ],
        prompt_text="",
    )

    prompt_text = context.to_prompt_text()

    assert "quality_decision: 合格" in prompt_text
    assert "quality_score: 1.0" in prompt_text
    assert "improvement_points: 冒頭の引きを強くする" in prompt_text


def test_memory_context_to_prompt_text_works_with_old_record_without_quality():
    context = MemoryContext(
        records=[
            {
                "topic": "猫の意外な雑学",
                "status": "completed",
                "media_mode": "placeholder",
                "scene_count": 3,
                "asset_count": 3,
                "video_path": "outputs/videos/final_video.mp4",
                "summary": "古い履歴です。",
            }
        ],
        prompt_text="",
    )

    prompt_text = context.to_prompt_text()

    assert "topic: 猫の意外な雑学" in prompt_text
    assert "quality_decision" not in prompt_text
