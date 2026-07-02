import pytest

from company.core.quality import QualityResult
from company.core.retry import RetryDecision
from company.core.workflow_loop import WorkflowLoop, WorkflowLoopResult


class FakeTaskExecutor:
    def __init__(self):
        self.calls = 0

    def execute(self, task):
        self.calls += 1
        return {
            "content": {
                "attempt": self.calls,
                "task": task,
            }
        }


class FakeQualityChecker:
    def __init__(self, results):
        self.results = results
        self.calls = 0

    def check(self, artifact):
        index = min(self.calls, len(self.results) - 1)
        self.calls += 1
        return self.results[index]


class FakeRetryEngine:
    def __init__(self, decisions):
        self.decisions = decisions
        self.calls = []

    def decide(self, quality_result, attempt):
        self.calls.append(
            {
                "quality_result": quality_result,
                "attempt": attempt,
            }
        )
        index = min(len(self.calls) - 1, len(self.decisions) - 1)
        return self.decisions[index]


def test_workflow_loop_passes_on_first_attempt():
    task_executor = FakeTaskExecutor()
    quality_result = QualityResult(passed=True, score=1.0)
    retry_decision = RetryDecision(
        should_retry=False,
        reason="quality passed",
        attempt=1,
        max_attempts=3,
    )
    loop = WorkflowLoop(
        task_executor=task_executor,
        quality_checker=FakeQualityChecker([quality_result]),
        retry_engine=FakeRetryEngine([retry_decision]),
    )

    result = loop.run(task={"task_id": "task_001"})

    assert result.attempts == 1
    assert task_executor.calls == 1
    assert result.quality_result == quality_result
    assert result.retry_decision == retry_decision


def test_workflow_loop_retries_after_quality_failure():
    task_executor = FakeTaskExecutor()
    first_quality = QualityResult(
        passed=False,
        score=0.4,
        reasons=["too short"],
        suggestions=["add detail"],
    )
    final_quality = QualityResult(passed=True, score=0.9)
    retry_decisions = [
        RetryDecision(
            should_retry=True,
            reason="quality failed",
            attempt=1,
            max_attempts=3,
            suggestions=["add detail"],
        ),
        RetryDecision(
            should_retry=False,
            reason="quality passed",
            attempt=2,
            max_attempts=3,
        ),
    ]
    retry_engine = FakeRetryEngine(retry_decisions)
    loop = WorkflowLoop(
        task_executor=task_executor,
        quality_checker=FakeQualityChecker([first_quality, final_quality]),
        retry_engine=retry_engine,
    )

    result = loop.run(task={"task_id": "task_retry"})

    assert result.attempts == 2
    assert task_executor.calls == 2
    assert result.quality_result == final_quality
    assert result.retry_decision == retry_decisions[1]
    assert [call["attempt"] for call in retry_engine.calls] == [1, 2]


def test_workflow_loop_stops_when_retry_limit_is_reached():
    task_executor = FakeTaskExecutor()
    failed_quality = QualityResult(
        passed=False,
        score=0.2,
        reasons=["missing content"],
    )
    retry_decisions = [
        RetryDecision(
            should_retry=True,
            reason="quality failed",
            attempt=1,
            max_attempts=3,
        ),
        RetryDecision(
            should_retry=True,
            reason="quality failed",
            attempt=2,
            max_attempts=3,
        ),
        RetryDecision(
            should_retry=False,
            reason="quality failed; max attempts reached",
            attempt=3,
            max_attempts=3,
        ),
    ]
    retry_engine = FakeRetryEngine(retry_decisions)
    loop = WorkflowLoop(
        task_executor=task_executor,
        quality_checker=FakeQualityChecker([failed_quality]),
        retry_engine=retry_engine,
    )

    result = loop.run(task={"task_id": "task_max"})

    assert result.attempts == 3
    assert task_executor.calls == 3
    assert result.retry_decision == retry_decisions[2]
    assert [call["attempt"] for call in retry_engine.calls] == [1, 2, 3]


def test_workflow_loop_returns_final_artifact():
    task_executor = FakeTaskExecutor()
    loop = WorkflowLoop(
        task_executor=task_executor,
        quality_checker=FakeQualityChecker([QualityResult(passed=True, score=1.0)]),
        retry_engine=FakeRetryEngine(
            [
                RetryDecision(
                    should_retry=False,
                    reason="quality passed",
                    attempt=1,
                    max_attempts=3,
                )
            ]
        ),
    )

    result = loop.run(task={"task_id": "task_artifact"})

    assert result.artifact == {
        "content": {
            "attempt": 1,
            "task": {"task_id": "task_artifact"},
        }
    }


def test_workflow_loop_returns_final_quality_result():
    final_quality = QualityResult(
        passed=True,
        score=0.95,
        reasons=["clear"],
        suggestions=["keep style"],
    )
    loop = WorkflowLoop(
        task_executor=FakeTaskExecutor(),
        quality_checker=FakeQualityChecker([final_quality]),
        retry_engine=FakeRetryEngine(
            [
                RetryDecision(
                    should_retry=False,
                    reason="quality passed",
                    attempt=1,
                    max_attempts=3,
                )
            ]
        ),
    )

    result = loop.run(task={"task_id": "task_quality"})

    assert result.quality_result == final_quality


def test_workflow_loop_returns_final_retry_decision():
    final_decision = RetryDecision(
        should_retry=False,
        reason="quality passed",
        attempt=1,
        max_attempts=3,
    )
    loop = WorkflowLoop(
        task_executor=FakeTaskExecutor(),
        quality_checker=FakeQualityChecker([QualityResult(passed=True, score=1.0)]),
        retry_engine=FakeRetryEngine([final_decision]),
    )

    result = loop.run(task={"task_id": "task_decision"})

    assert result.retry_decision == final_decision


def test_workflow_loop_attempts_increment_correctly():
    retry_engine = FakeRetryEngine(
        [
            RetryDecision(
                should_retry=True,
                reason="quality failed",
                attempt=1,
                max_attempts=3,
            ),
            RetryDecision(
                should_retry=True,
                reason="quality failed",
                attempt=2,
                max_attempts=3,
            ),
            RetryDecision(
                should_retry=False,
                reason="quality passed",
                attempt=3,
                max_attempts=3,
            ),
        ]
    )
    loop = WorkflowLoop(
        task_executor=FakeTaskExecutor(),
        quality_checker=FakeQualityChecker(
            [
                QualityResult(passed=False, score=0.4),
                QualityResult(passed=False, score=0.6),
                QualityResult(passed=True, score=0.9),
            ]
        ),
        retry_engine=retry_engine,
    )

    result = loop.run(task={"task_id": "task_attempts"})

    assert result.attempts == 3
    assert [call["attempt"] for call in retry_engine.calls] == [1, 2, 3]


def test_workflow_loop_result_attempts_less_than_one_raises_value_error():
    with pytest.raises(ValueError):
        WorkflowLoopResult(
            artifact={"content": "artifact"},
            quality_result=QualityResult(passed=True, score=1.0),
            retry_decision=RetryDecision(
                should_retry=False,
                reason="quality passed",
                attempt=0,
                max_attempts=3,
            ),
            attempts=0,
        )
