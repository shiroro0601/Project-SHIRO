from company.core.ceo_decision import (
    ACTION_PROCEED,
    ACTION_RESEARCH_AGAIN,
    ACTION_REVISE,
    ACTION_STOP,
    CEODecisionPolicy,
)
from company.reports.quality_feedback import QualityFeedback


def feedback(decision: str, score: float):
    return QualityFeedback(
        evaluation="evaluation",
        improvement_points="improvement",
        decision=decision,
        score=score,
    )


def test_ceo_decision_without_feedback_proceeds():
    decision = CEODecisionPolicy().decide(stage="review")

    assert decision.action == ACTION_PROCEED
    assert decision.stage == "review"


def test_ceo_decision_approved_feedback_proceeds():
    decision = CEODecisionPolicy().decide(
        stage="review",
        quality_feedback=feedback("合格", 1.0),
    )

    assert decision.action == ACTION_PROCEED
    assert decision.quality_decision == "合格"
    assert decision.quality_score == 1.0


def test_ceo_decision_revision_with_retry_remaining_revises():
    decision = CEODecisionPolicy().decide(
        stage="review",
        quality_feedback=feedback("修正必要", 0.0),
        retry_count=0,
        retry_limit=2,
    )

    assert decision.action == ACTION_REVISE
    assert "retry remains" in decision.reason


def test_ceo_decision_revision_at_retry_limit_stops():
    decision = CEODecisionPolicy().decide(
        stage="review",
        quality_feedback=feedback("修正必要", 0.0),
        retry_count=2,
        retry_limit=2,
    )

    assert decision.action == ACTION_STOP
    assert "retry limit" in decision.reason


def test_ceo_decision_unknown_stops():
    decision = CEODecisionPolicy().decide(
        stage="review",
        quality_feedback=feedback("不明", 0.5),
    )

    assert decision.action == ACTION_STOP
    assert decision.reason == "Reviewer decision is unknown."


def test_ceo_decision_research_missing_requests_research_again():
    decision = CEODecisionPolicy().decide(
        stage="review",
        quality_feedback=feedback("合格", 1.0),
        context={"research_missing": True},
    )

    assert decision.action == ACTION_RESEARCH_AGAIN
    assert decision.metadata["research_missing"] is True


def test_ceo_decision_research_missing_has_priority():
    decision = CEODecisionPolicy().decide(
        stage="review",
        quality_feedback=feedback("修正必要", 0.0),
        retry_count=0,
        retry_limit=2,
        context={"research_missing": True},
    )

    assert decision.action == ACTION_RESEARCH_AGAIN
