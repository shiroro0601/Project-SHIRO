from company.core.quality import QualityResult
from company.core.retry import RetryDecision
from company.core.workflow_loop import WorkflowLoop
from company.core.workflow_observer import CompositeWorkflowLoopObserver


class FakeTaskExecutor:
    def __init__(self):
        self.calls = 0

    def execute(self, task):
        self.calls += 1
        return {
            "content": {
                "attempt": self.calls,
                "task_id": task["task_id"],
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
        self.calls = 0

    def decide(self, quality_result, attempt):
        index = min(self.calls, len(self.decisions) - 1)
        self.calls += 1
        return self.decisions[index]


class RecordingObserver:
    def __init__(self):
        self.events = []

    def on_task_started(self, task, attempt):
        self.events.append(("task_started", task, attempt))

    def on_artifact_created(self, task, artifact, attempt):
        self.events.append(("artifact_created", task, artifact, attempt))

    def on_quality_checked(self, task, quality_result, attempt):
        self.events.append(("quality_checked", task, quality_result, attempt))

    def on_retry_decided(self, task, retry_decision, attempt):
        self.events.append(("retry_decided", task, retry_decision, attempt))

    def on_task_finished(self, task, result):
        self.events.append(("task_finished", task, result))


class FailingObserver(RecordingObserver):
    def on_task_started(self, task, attempt):
        super().on_task_started(task, attempt)
        raise RuntimeError("observer failed")


def _loop(observer=None, quality_results=None, retry_decisions=None):
    quality_results = quality_results or [QualityResult(passed=True, score=1.0)]
    retry_decisions = retry_decisions or [
        RetryDecision(
            should_retry=False,
            reason="quality passed",
            attempt=1,
            max_attempts=3,
        )
    ]
    return WorkflowLoop(
        task_executor=FakeTaskExecutor(),
        quality_checker=FakeQualityChecker(quality_results),
        retry_engine=FakeRetryEngine(retry_decisions),
        observer=observer,
    )


def test_workflow_loop_runs_without_observer():
    loop = _loop()

    result = loop.run({"task_id": "task_no_observer"})

    assert result.attempts == 1


def test_observer_on_task_started_is_called():
    observer = RecordingObserver()

    _loop(observer=observer).run({"task_id": "task_started"})

    assert observer.events[0] == ("task_started", {"task_id": "task_started"}, 1)


def test_observer_on_artifact_created_is_called():
    observer = RecordingObserver()

    _loop(observer=observer).run({"task_id": "task_artifact"})

    event = observer.events[1]
    assert event[0] == "artifact_created"
    assert event[1] == {"task_id": "task_artifact"}
    assert event[2] == {
        "content": {
            "attempt": 1,
            "task_id": "task_artifact",
        }
    }
    assert event[3] == 1


def test_observer_on_quality_checked_is_called():
    observer = RecordingObserver()
    quality_result = QualityResult(passed=True, score=0.9)

    _loop(observer=observer, quality_results=[quality_result]).run({"task_id": "task_quality"})

    assert observer.events[2] == (
        "quality_checked",
        {"task_id": "task_quality"},
        quality_result,
        1,
    )


def test_observer_on_retry_decided_is_called():
    observer = RecordingObserver()
    retry_decision = RetryDecision(
        should_retry=False,
        reason="quality passed",
        attempt=1,
        max_attempts=3,
    )

    _loop(observer=observer, retry_decisions=[retry_decision]).run({"task_id": "task_retry"})

    assert observer.events[3] == (
        "retry_decided",
        {"task_id": "task_retry"},
        retry_decision,
        1,
    )


def test_observer_on_task_finished_is_called():
    observer = RecordingObserver()

    result = _loop(observer=observer).run({"task_id": "task_finished"})

    assert observer.events[4] == (
        "task_finished",
        {"task_id": "task_finished"},
        result,
    )


def test_observer_events_are_called_for_each_attempt_when_retrying():
    observer = RecordingObserver()
    quality_results = [
        QualityResult(passed=False, score=0.2, reasons=["too short"]),
        QualityResult(passed=True, score=0.9),
    ]
    retry_decisions = [
        RetryDecision(
            should_retry=True,
            reason="quality failed",
            attempt=1,
            max_attempts=3,
        ),
        RetryDecision(
            should_retry=False,
            reason="quality passed",
            attempt=2,
            max_attempts=3,
        ),
    ]

    result = _loop(
        observer=observer,
        quality_results=quality_results,
        retry_decisions=retry_decisions,
    ).run({"task_id": "task_retry_events"})

    per_attempt_events = [event for event in observer.events if event[0] != "task_finished"]
    assert result.attempts == 2
    assert [event[0] for event in per_attempt_events] == [
        "task_started",
        "artifact_created",
        "quality_checked",
        "retry_decided",
        "task_started",
        "artifact_created",
        "quality_checked",
        "retry_decided",
    ]
    assert [event[-1] for event in per_attempt_events] == [1, 1, 1, 1, 2, 2, 2, 2]


def test_composite_workflow_loop_observer_calls_multiple_observers():
    first_observer = RecordingObserver()
    second_observer = RecordingObserver()
    composite = CompositeWorkflowLoopObserver([first_observer, second_observer])

    _loop(observer=composite).run({"task_id": "task_composite"})

    assert [event[0] for event in first_observer.events] == [
        "task_started",
        "artifact_created",
        "quality_checked",
        "retry_decided",
        "task_finished",
    ]
    assert first_observer.events == second_observer.events


def test_composite_workflow_loop_observer_keeps_notifying_after_observer_error():
    failing_observer = FailingObserver()
    healthy_observer = RecordingObserver()
    composite = CompositeWorkflowLoopObserver([failing_observer, healthy_observer])

    _loop(observer=composite).run({"task_id": "task_error"})

    assert len(composite.errors) == 1
    assert isinstance(composite.errors[0], RuntimeError)
    assert [event[0] for event in healthy_observer.events] == [
        "task_started",
        "artifact_created",
        "quality_checked",
        "retry_decided",
        "task_finished",
    ]
