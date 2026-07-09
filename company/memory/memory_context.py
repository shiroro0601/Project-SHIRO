from dataclasses import dataclass


@dataclass
class MemoryContext:
    records: list[dict]
    prompt_text: str

    def is_empty(self) -> bool:
        return len(self.records) == 0

    def to_prompt_text(self) -> str:
        if not self.prompt_text and self.records:
            return self._build_prompt_text()
        return self.prompt_text

    def _build_prompt_text(self) -> str:
        lines = ["過去の実行履歴:"]
        for index, record in enumerate(self.records, start=1):
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
            quality_lines = self._quality_lines(record)
            if quality_lines:
                lines.extend(quality_lines)
        return "\n".join(lines)

    def _quality_lines(self, record: dict) -> list[str]:
        lines = []
        if "quality_decision" in record:
            lines.append(f"   quality_decision: {record.get('quality_decision', '')}")
        if "quality_score" in record:
            lines.append(f"   quality_score: {record.get('quality_score', '')}")
        if "improvement_points" in record:
            lines.append(
                f"   improvement_points: {record.get('improvement_points', '')}"
            )
        return lines
