import re
from dataclasses import dataclass


@dataclass
class QualityFeedback:
    evaluation: str
    improvement_points: str
    decision: str
    score: float


class QualityFeedbackParser:
    def parse(self, review_result: str) -> QualityFeedback:
        text = str(review_result or "").strip()
        evaluation = self._extract_section(text, "評価")
        improvement_points = self._extract_section(text, "改善点")
        decision_text = self._extract_section(text, "判定")
        decision = self._normalize_decision(decision_text)

        if not evaluation and not improvement_points and decision == "不明":
            return QualityFeedback(
                evaluation=text,
                improvement_points="",
                decision="不明",
                score=0.5,
            )

        return QualityFeedback(
            evaluation=evaluation,
            improvement_points=improvement_points,
            decision=decision,
            score=self._score_for_decision(decision),
        )

    def _extract_section(self, text: str, section_name: str) -> str:
        pattern = (
            rf"【{re.escape(section_name)}】\s*"
            rf"(.*?)(?=\n\s*【[^】]+】|\Z)"
        )
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()

    def _normalize_decision(self, decision_text: str) -> str:
        first_line = decision_text.strip().splitlines()[0].strip() if decision_text else ""
        if first_line == "合格":
            return "合格"
        if first_line == "修正必要":
            return "修正必要"
        if "修正必要" in first_line:
            return "修正必要"
        if "合格" in first_line:
            return "合格"
        return "不明"

    def _score_for_decision(self, decision: str) -> float:
        if decision == "合格":
            return 1.0
        if decision == "修正必要":
            return 0.0
        return 0.5
