from dataclasses import dataclass, field
from typing import Any, List, Protocol


@dataclass
class QualityResult:
    passed: bool
    score: float
    reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0.")


class QualityRule(Protocol):
    def check(self, artifact: Any) -> QualityResult:
        ...


class BasicQualityRule:
    def check(self, artifact: Any) -> QualityResult:
        if artifact is None:
            return QualityResult(
                passed=False,
                score=0.0,
                reasons=["artifact is None"],
                suggestions=["Provide an artifact before quality checking."],
            )

        if not self._has_content(artifact):
            return QualityResult(
                passed=False,
                score=0.0,
                reasons=["artifact content is missing"],
                suggestions=["Add content to the artifact."],
            )

        content = self._get_content(artifact)

        if self._is_empty_content(content):
            return QualityResult(
                passed=False,
                score=0.0,
                reasons=["artifact content is empty"],
                suggestions=["Provide non-empty artifact content."],
            )

        return QualityResult(
            passed=True,
            score=1.0,
            reasons=["artifact content is present"],
            suggestions=[],
        )

    def _has_content(self, artifact: Any) -> bool:
        if isinstance(artifact, dict):
            return "content" in artifact

        return hasattr(artifact, "content")

    def _get_content(self, artifact: Any) -> Any:
        if isinstance(artifact, dict):
            return artifact.get("content")

        return getattr(artifact, "content")

    def _is_empty_content(self, content: Any) -> bool:
        if content is None:
            return True

        if isinstance(content, str):
            return content.strip() == ""

        if isinstance(content, dict):
            return len(content) == 0

        if isinstance(content, (list, tuple, set)):
            return len(content) == 0

        return False


class QualityChecker:
    def __init__(self, rules: List[QualityRule] | None = None):
        self.rules = rules or [BasicQualityRule()]

    def check(self, artifact: Any) -> QualityResult:
        results = [rule.check(artifact) for rule in self.rules]

        passed = all(result.passed for result in results)
        score = sum(result.score for result in results) / len(results)
        reasons: List[str] = []
        suggestions: List[str] = []

        for result in results:
            reasons.extend(result.reasons)
            suggestions.extend(result.suggestions)

        return QualityResult(
            passed=passed,
            score=score,
            reasons=reasons,
            suggestions=suggestions,
        )
