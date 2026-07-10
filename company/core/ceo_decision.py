from dataclasses import asdict, dataclass, field


ACTION_PROCEED = "proceed"
ACTION_REVISE = "revise"
ACTION_RESEARCH_AGAIN = "research_again"
ACTION_STOP = "stop"


@dataclass
class CEODecision:
    action: str
    reason: str
    stage: str
    quality_decision: str
    quality_score: float
    retry_count: int
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class CEODecisionPolicy:
    def decide(
        self,
        *,
        stage: str,
        quality_feedback=None,
        retry_count: int = 0,
        retry_limit: int = 0,
        context: dict | None = None,
    ) -> CEODecision:
        context = context or {}
        quality_decision = self._quality_decision(quality_feedback)
        quality_score = self._quality_score(quality_feedback)

        if context.get("research_missing") is True:
            return CEODecision(
                action=ACTION_RESEARCH_AGAIN,
                reason="Research result is missing and should be regenerated.",
                stage=stage,
                quality_decision=quality_decision,
                quality_score=quality_score,
                retry_count=retry_count,
                metadata=dict(context),
            )

        if quality_feedback is None:
            return CEODecision(
                action=ACTION_PROCEED,
                reason="No quality feedback is available, so continue by default.",
                stage=stage,
                quality_decision=quality_decision,
                quality_score=quality_score,
                retry_count=retry_count,
                metadata=dict(context),
            )

        if quality_decision == "合格":
            return CEODecision(
                action=ACTION_PROCEED,
                reason="Reviewer approved the script.",
                stage=stage,
                quality_decision=quality_decision,
                quality_score=quality_score,
                retry_count=retry_count,
                metadata=dict(context),
            )

        if quality_decision == "修正必要" and retry_count < retry_limit:
            return CEODecision(
                action=ACTION_REVISE,
                reason="Reviewer requested revision and retry remains.",
                stage=stage,
                quality_decision=quality_decision,
                quality_score=quality_score,
                retry_count=retry_count,
                metadata=dict(context),
            )

        if quality_decision == "修正必要":
            return CEODecision(
                action=ACTION_STOP,
                reason="Reviewer requested revision but retry limit was reached.",
                stage=stage,
                quality_decision=quality_decision,
                quality_score=quality_score,
                retry_count=retry_count,
                metadata=dict(context),
            )

        if quality_decision == "不明":
            return CEODecision(
                action=ACTION_STOP,
                reason="Reviewer decision is unknown.",
                stage=stage,
                quality_decision=quality_decision,
                quality_score=quality_score,
                retry_count=retry_count,
                metadata=dict(context),
            )

        return CEODecision(
            action=ACTION_PROCEED,
            reason="No blocking condition was found.",
            stage=stage,
            quality_decision=quality_decision,
            quality_score=quality_score,
            retry_count=retry_count,
            metadata=dict(context),
        )

    def _quality_decision(self, quality_feedback) -> str:
        if quality_feedback is None:
            return ""
        if isinstance(quality_feedback, dict):
            return str(quality_feedback.get("decision", ""))
        return str(getattr(quality_feedback, "decision", ""))

    def _quality_score(self, quality_feedback) -> float:
        if quality_feedback is None:
            return 0.0
        if isinstance(quality_feedback, dict):
            value = quality_feedback.get("score", 0.0)
        else:
            value = getattr(quality_feedback, "score", 0.0)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
