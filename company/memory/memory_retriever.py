from company.memory.memory_context import MemoryContext


EMPTY_PROMPT_TEXT = "過去の実行履歴はありません。"


class MemoryRetriever:
    def __init__(self, memory):
        self.memory = memory

    def get_recent_run_reports(self, limit: int = 3) -> list[dict]:
        if limit < 1:
            return []

        data = self._load_memory_data()
        run_reports = data.get("run_reports", [])
        if not isinstance(run_reports, list):
            return []

        return list(reversed(run_reports[-limit:]))

    def build_context(self, limit: int = 3) -> MemoryContext:
        records = self.get_recent_run_reports(limit=limit)
        if not records:
            return MemoryContext(records=[], prompt_text=EMPTY_PROMPT_TEXT)

        return MemoryContext(
            records=records,
            prompt_text=self._build_prompt_text(records),
        )

    def _load_memory_data(self) -> dict:
        if hasattr(self.memory, "load"):
            data = self.memory.load()
            return data if isinstance(data, dict) else {}

        data = getattr(self.memory, "data", {})
        return data if isinstance(data, dict) else {}

    def _build_prompt_text(self, records: list[dict]) -> str:
        lines = ["過去の実行履歴:"]
        for index, record in enumerate(records, start=1):
            lines.extend(
                [
                    f"{index}. topic: {record.get('topic', '')}",
                    f"   status: {record.get('status', '')}",
                    f"   media_mode: {record.get('media_mode', '')}",
                    f"   scene_count: {record.get('scene_count', 0)}",
                    f"   asset_count: {record.get('asset_count', 0)}",
                    f"   video_path: {record.get('video_path', '')}",
                    f"   summary: {record.get('summary', '')}",
                ]
            )
        return "\n".join(lines)
