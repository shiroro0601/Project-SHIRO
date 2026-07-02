import pytest

from company.core.quality import QualityResult
from company.core.retry import RetryDecision, RetryEngine, RetryPolicy


def test_retry_policy_can_be_created():
    policy = RetryPolicy(max_attempts=5, min_score=0.8)

    assert policy.max_attempts == 5
    assert policy.min_score == 0.8


def test_retry_policy_max_attempts_zero_raises_value_error():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_retry_policy_min_score_below_zero_raises_value_error():
    with pytest.raises(ValueError):
        RetryPolicy(min_score=-0.1)


def test_retry_policy_min_score_above_one_raises_value_error():
    with pytest.raises(ValueError):
        RetryPolicy(min_score=1.1)


def test_retry_decision_can_be_created():
    decision = RetryDecision(
        should_retry=True,
        reason="quality failed",
        attempt=1,
        max_attempts=3,
        suggestions=["improve detail"],
    )

    assert decision.should_retry is True
    assert decision.reason == "quality failed"
    assert decision.attempt == 1
    assert decision.max_attempts == 3
    assert decision.suggestions == ["improve detail"]


def test_retry_decision_attempt_above_max_attempts_raises_value_error():
    with pytest.raises(ValueError):
        RetryDecision(
            should_retry=False,
            reason="invalid",
            attempt=4,
            max_attempts=3,
        )


def test_retry_decision_negative_attempt_raises_value_error():
    with pytest.raises(ValueError):
        RetryDecision(
            should_retry=False,
            reason="invalid",
            attempt=-1,
            max_attempts=3,
        )


def test_passed_quality_with_sufficient_score_does_not_retry():
    quality_result = QualityResult(passed=True, score=0.9)
    engine = RetryEngine(policy=RetryPolicy(max_attempts=3, min_score=0.7))

    decision = engine.decide(quality_result, attempt=0)

    assert decision.should_retry is False
    assert decision.reason == "quality passed and score is sufficient"


def test_failed_quality_retries_when_attempt_is_under_max_attempts():
    quality_result = QualityResult(
        passed=False,
        score=0.9,
        reasons=["missing details"],
    )
    engine = RetryEngine(policy=RetryPolicy(max_attempts=3, min_score=0.7))

    decision = engine.decide(quality_result, attempt=1)

    assert decision.should_retry is True
    assert "quality failed" in decision.reason
    assert "missing details" in decision.reason


def test_low_score_retries_when_attempt_is_under_max_attempts():
    quality_result = QualityResult(passed=True, score=0.4)
    engine = RetryEngine(policy=RetryPolicy(max_attempts=3, min_score=0.7))

    decision = engine.decide(quality_result, attempt=1)

    assert decision.should_retry is True
    assert "below min_score" in decision.reason


def test_retry_stops_when_attempt_reaches_max_attempts():
    quality_result = QualityResult(
        passed=False,
        score=0.2,
        reasons=["too short"],
    )
    engine = RetryEngine(policy=RetryPolicy(max_attempts=3, min_score=0.7))

    decision = engine.decide(quality_result, attempt=3)

    assert decision.should_retry is False
    assert "max attempts reached" in decision.reason


def test_retry_decision_inherits_suggestions():
    quality_result = QualityResult(
        passed=False,
        score=0.2,
        suggestions=["add examples", "make it clearer"],
    )
    engine = RetryEngine()

    decision = engine.decide(quality_result, attempt=0)

    assert decision.suggestions == ["add examples", "make it clearer"]


def test_retry_engine_uses_default_policy_when_not_specified():
    engine = RetryEngine()

    assert engine.policy.max_attempts == 3
    assert engine.policy.min_score == 0.7

    decision = engine.decide(QualityResult(passed=True, score=0.6), attempt=0)

    assert decision.should_retry is True
    assert decision.max_attempts == 3
