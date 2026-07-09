from company.memory.memory_context import MemoryContext


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
        return MemoryContext(records=records)

    def _load_memory_data(self) -> dict:
        if hasattr(self.memory, "load"):
            data = self.memory.load()
            return data if isinstance(data, dict) else {}

        data = getattr(self.memory, "data", {})
        return data if isinstance(data, dict) else {}
