from dataclasses import dataclass


@dataclass
class MemoryContext:
    records: list[dict]
    prompt_text: str = ""

    def is_empty(self) -> bool:
        return len(self.records) == 0

    def to_prompt_text(self) -> str:
        if not self.prompt_text:
            return self._build_prompt_text()
        return self.prompt_text

    def _build_prompt_text(self) -> str:
        if not self.records:
            return "\n".join(
                [
                    "過去の実行履歴はありません。",
                    "成功パターンはまだありません。",
                    "避けるべき失敗パターンはまだありません。",
                    "今回意識する改善点はまだありません。",
                ]
            )

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
        lines.append("")
        lines.extend(self._success_pattern_lines())
        lines.append("")
        lines.extend(self._avoid_pattern_lines())
        lines.append("")
        lines.extend(self._improvement_focus_lines())
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
        if "approval_status" in record:
            lines.append(f"   approval_status: {record.get('approval_status', '')}")
        if "production_resumed" in record:
            lines.append(f"   production_resumed: {record.get('production_resumed', '')}")
        if "production_resume_completed" in record:
            lines.append(
                "   production_resume_completed: "
                f"{record.get('production_resume_completed', '')}"
            )
        return lines

    def _success_pattern_lines(self) -> list[str]:
        lines = ["成功パターン:"]
        success_records = [record for record in self.records if self._is_success(record)]
        if not success_records:
            lines.append("- まだありません。")
            return lines

        for record in success_records:
            lines.append(
                "- "
                f"topic: {record.get('topic', '')}; "
                f"script_title: {record.get('script_title', '')}; "
                f"scene_count: {record.get('scene_count', 0)}; "
                f"asset_count: {record.get('asset_count', 0)}; "
                f"summary: {record.get('summary', '')}"
            )
        return lines

    def _avoid_pattern_lines(self) -> list[str]:
        lines = ["避けること:"]
        avoid_records = [record for record in self.records if self._should_avoid(record)]
        if not avoid_records:
            lines.append("- まだありません。")
            return lines

        for record in avoid_records:
            stop_part = ""
            if record.get("stop_reason"):
                stop_part = f"stop_reason: {record.get('stop_reason', '')}; "
            approval_part = ""
            if record.get("approval_status"):
                approval_part = (
                    f"approval_status: {record.get('approval_status', '')}; "
                )
            lines.append(
                "- "
                f"topic: {record.get('topic', '')}; "
                f"{stop_part}"
                f"{approval_part}"
                f"improvement_points: {record.get('improvement_points', '')}; "
                f"summary: {record.get('summary', '')}"
            )
        return lines

    def _improvement_focus_lines(self) -> list[str]:
        lines = ["今回意識すること:"]
        improvement_points = self._unique_improvement_points()
        if not improvement_points:
            lines.append("- 過去の改善点はありません。")
            return lines

        for point in improvement_points:
            lines.append(f"- {point}")
        return lines

    def _unique_improvement_points(self) -> list[str]:
        seen = set()
        points = []
        for record in self.records:
            raw_points = str(record.get("improvement_points", "") or "").strip()
            if not raw_points:
                continue
            for point in self._split_improvement_points(raw_points):
                if point not in seen:
                    seen.add(point)
                    points.append(point)
        return points

    def _split_improvement_points(self, raw_points: str) -> list[str]:
        normalized = raw_points.replace("\r\n", "\n").replace("\r", "\n")
        candidates = []
        for line in normalized.split("\n"):
            value = line.strip()
            if value.startswith("-"):
                value = value[1:].strip()
            if value:
                candidates.append(value)
        return candidates

    def _is_success(self, record: dict) -> bool:
        if record.get("quality_decision") == "合格":
            return True
        score = self._quality_score(record)
        return score is not None and score >= 0.8

    def _should_avoid(self, record: dict) -> bool:
        if record.get("approval_status") in {"pending", "rejected"}:
            return True
        if record.get("stopped"):
            return True
        if record.get("quality_decision") == "修正必要":
            return True
        score = self._quality_score(record)
        return score is not None and score <= 0.3

    def _quality_score(self, record: dict):
        if "quality_score" not in record:
            return None
        try:
            return float(record.get("quality_score"))
        except (TypeError, ValueError):
            return None
