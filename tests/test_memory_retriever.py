from company.memory.memory_retriever import MemoryRetriever


class FakeMemory:
    def __init__(self, data):
        self.data = data

    def load(self):
        return self.data


def make_record(topic: str, created_at: str) -> dict:
    return {
        "type": "real_ai_company_run",
        "topic": topic,
        "created_at": created_at,
        "media_mode": "placeholder",
        "status": "completed",
        "script_title": f"{topic} title",
        "scene_count": 3,
        "asset_count": 3,
        "video_path": f"outputs/videos/{topic}.mp4",
        "scene_video_path": f"outputs/videos/{topic}.mp4",
        "summary": f"{topic} を placeholder mode で制作しました。",
    }


def test_memory_retriever_returns_empty_context_without_run_reports():
    retriever = MemoryRetriever(FakeMemory({"jobs": []}))

    context = retriever.build_context()

    assert context.is_empty() is True
    assert context.records == []
    assert "過去の実行履歴はありません。" in context.to_prompt_text()
    assert "成功パターンはまだありません。" in context.to_prompt_text()


def test_memory_retriever_gets_recent_run_reports_with_limit():
    records = [
        make_record("topic1", "2026-07-09T10:00:00"),
        make_record("topic2", "2026-07-09T10:01:00"),
        make_record("topic3", "2026-07-09T10:02:00"),
    ]
    retriever = MemoryRetriever(FakeMemory({"run_reports": records}))

    recent = retriever.get_recent_run_reports(limit=2)

    assert [record["topic"] for record in recent] == ["topic3", "topic2"]


def test_memory_retriever_builds_prompt_text_newest_first():
    records = [
        make_record("古いテーマ", "2026-07-09T10:00:00"),
        make_record("新しいテーマ", "2026-07-09T10:01:00"),
    ]
    retriever = MemoryRetriever(FakeMemory({"run_reports": records}))

    context = retriever.build_context(limit=2)
    prompt_text = context.to_prompt_text()

    assert context.is_empty() is False
    assert context.records[0]["topic"] == "新しいテーマ"
    assert "過去の実行履歴:" in prompt_text
    assert "1. topic: 新しいテーマ" in prompt_text
    assert "2. topic: 古いテーマ" in prompt_text
    assert "summary: 新しいテーマ を placeholder mode で制作しました。" in prompt_text
    assert "成功パターン:" in prompt_text
    assert "避けること:" in prompt_text
    assert "今回意識すること:" in prompt_text
