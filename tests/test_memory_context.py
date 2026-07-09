from company.memory.memory_context import MemoryContext


def test_memory_context_is_empty_when_records_are_empty():
    context = MemoryContext(records=[])

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


def test_memory_context_to_prompt_text_for_empty_records_has_guidance_sections():
    context = MemoryContext(records=[])

    prompt_text = context.to_prompt_text()

    assert "過去の実行履歴はありません。" in prompt_text
    assert "成功パターンはまだありません。" in prompt_text
    assert "避けるべき失敗パターンはまだありません。" in prompt_text
    assert "今回意識する改善点はまだありません。" in prompt_text


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
    assert "成功パターン:" in prompt_text
    assert "script_title:" in prompt_text
    assert "今回意識すること:" in prompt_text


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
    assert "成功パターン:" in prompt_text
    assert "- まだありません。" in prompt_text


def test_memory_context_high_score_record_goes_to_success_patterns():
    context = MemoryContext(
        records=[
            {
                "topic": "犬の雑学",
                "script_title": "犬タイトル",
                "scene_count": 2,
                "asset_count": 2,
                "summary": "犬動画を制作しました。",
                "quality_score": 0.9,
            }
        ]
    )

    prompt_text = context.to_prompt_text()

    assert "成功パターン:" in prompt_text
    assert "topic: 犬の雑学; script_title: 犬タイトル" in prompt_text


def test_memory_context_passed_decision_record_goes_to_success_patterns():
    context = MemoryContext(
        records=[
            {
                "topic": "猫の雑学",
                "script_title": "猫タイトル",
                "scene_count": 3,
                "asset_count": 3,
                "summary": "品質判定: 合格。",
                "quality_decision": "合格",
                "quality_score": 0.5,
            }
        ]
    )

    prompt_text = context.to_prompt_text()

    assert "成功パターン:" in prompt_text
    assert "topic: 猫の雑学; script_title: 猫タイトル" in prompt_text


def test_memory_context_low_score_record_goes_to_avoid_patterns():
    context = MemoryContext(
        records=[
            {
                "topic": "鳥の雑学",
                "summary": "説明が弱いです。",
                "quality_score": 0.2,
                "improvement_points": "冒頭の引きを強くする",
            }
        ]
    )

    prompt_text = context.to_prompt_text()

    assert "避けること:" in prompt_text
    assert "topic: 鳥の雑学; improvement_points: 冒頭の引きを強くする" in prompt_text


def test_memory_context_revision_required_record_goes_to_avoid_patterns():
    context = MemoryContext(
        records=[
            {
                "topic": "魚の雑学",
                "summary": "品質判定: 修正必要。",
                "quality_decision": "修正必要",
                "quality_score": 1.0,
                "improvement_points": "本編を3点に整理する",
            }
        ]
    )

    prompt_text = context.to_prompt_text()

    assert "避けること:" in prompt_text
    assert "topic: 魚の雑学; improvement_points: 本編を3点に整理する" in prompt_text


def test_memory_context_deduplicates_improvement_points():
    context = MemoryContext(
        records=[
            {"improvement_points": "冒頭の引きを強くする\n本編を3点に整理する"},
            {"improvement_points": "冒頭の引きを強くする"},
        ]
    )

    prompt_text = context.to_prompt_text()

    assert prompt_text.count("- 冒頭の引きを強くする") == 1
    assert "- 本編を3点に整理する" in prompt_text


def test_memory_context_without_improvement_points_has_empty_message():
    context = MemoryContext(records=[{"topic": "猫の雑学"}])

    prompt_text = context.to_prompt_text()

    assert "- 過去の改善点はありません。" in prompt_text
