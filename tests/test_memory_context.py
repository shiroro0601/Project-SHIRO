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
