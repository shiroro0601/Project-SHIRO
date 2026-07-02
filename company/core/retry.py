from dataclasses import dataclass, field
from typing import List

from company.core.quality import QualityResult


@dataclass
class RetryDecision:
    should_retry: bool
    reason: str
    attempt: int
    max_attempts: int
    suggestions: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.attempt < 0:
            raise ValueError("attempt must be greater than or equal to 0.")

        if self.max_attempts < 1:
            raise ValueError("max_attempts must be greater than or equal to 1.")

        if self.attempt > self.max_attempts:
            raise ValueError("attempt must not be greater than max_attempts.")


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    min_score: float = 0.7

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be greater than or equal to 1.")

        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0.")


class RetryEngine:
    """
    QualityResultをもとに再試行すべきか判断する層。

    再実行そのものは行わず、Workflow/Brain/Provider/Conversation/CompanyMemoryにも依存しない。
    """

    def __init__(self, policy: RetryPolicy | None = None):
        self.policy = policy or RetryPolicy()

    def decide(self, quality_result: QualityResult, attempt: int) -> RetryDecision:
        retry_reasons = self._retry_reasons(quality_result)
        is_retry_candidate = len(retry_reasons) > 0
        can_retry = attempt < self.policy.max_attempts
        should_retry = is_retry_candidate and can_retry

        if should_retry:
            reason = "; ".join(retry_reasons)
        elif is_retry_candidate:
            reason = "; ".join(retry_reasons + ["max attempts reached"])
        else:
            reason = "quality passed and score is sufficient"

        return RetryDecision(
            should_retry=should_retry,
            reason=reason,
            attempt=attempt,
            max_attempts=self.policy.max_attempts,
            suggestions=list(quality_result.suggestions),
        )

    def _retry_reasons(self, quality_result: QualityResult) -> List[str]:
        reasons: List[str] = []

        if not quality_result.passed:
            if quality_result.reasons:
                reasons.append("quality failed: " + ", ".join(quality_result.reasons))
            else:
                reasons.append("quality failed")

        if quality_result.score < self.policy.min_score:
            reasons.append(
                f"score {quality_result.score} is below min_score {self.policy.min_score}"
            )

        return reasons
