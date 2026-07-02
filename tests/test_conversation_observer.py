from company.core.conversation import ConversationManager
from company.core.conversation_observer import ConversationObserver
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


def _observer(manager=None, conversation_id="workflow_001", employee_name="WorkflowLoop"):
    return ConversationObserver(
        conversation_manager=manager or ConversationManager(),
        conversation_id=conversation_id,
        employee_name=employee_name,
    )


def _messages(manager, conversation_id="workflow_001"):
    return manager.get_messages(conversation_id)


def test_on_task_started_adds_message():
    manager = ConversationManager()
    observer = _observer(manager=manager)

    observer.on_task_started({"task_id": "task_001"}, attempt=1)

    messages = _messages(manager)
    assert len(messages) == 1
    assert messages[0].content == "Task started: {'task_id': 'task_001'}"


def test_on_artifact_created_adds_message():
    manager = ConversationManager()
    observer = _observer(manager=manager)

    observer.on_artifact_created(
        {"task_id": "task_001"},
        {"content": {"plan": "test"}},
        attempt=2,
    )

    messages = _messages(manager)
    assert messages[0].content == "Artifact created on attempt 2"


def test_on_quality_checked_records_passed_and_score():
    manager = ConversationManager()
    observer = _observer(manager=manager)
    quality_result = QualityResult(passed=True, score=0.85)

    observer.on_quality_checked({"task_id": "task_001"}, quality_result, attempt=1)

    messages = _messages(manager)
    assert messages[0].content == "Quality checked: passed=True, score=0.85"


def test_on_retry_decided_records_should_retry_and_reason():
    manager = ConversationManager()
    observer = _observer(manager=manager)
    retry_decision = RetryDecision(
        should_retry=True,
        reason="quality failed",
        attempt=1,
        max_attempts=3,
    )

    observer.on_retry_decided({"task_id": "task_001"}, retry_decision, attempt=1)

    messages = _messages(manager)
    assert messages[0].content == (
        "Retry decided: should_retry=True, reason=quality failed"
    )


def test_on_task_finished_records_attempts():
    manager = ConversationManager()
    observer = _observer(manager=manager)
    result = WorkflowLoopResult(
        artifact={"content": {"plan": "test"}},
        quality_result=QualityResult(passed=True, score=1.0),
        retry_decision=RetryDecision(
            should_retry=False,
            reason="quality passed",
            attempt=2,
            max_attempts=3,
        ),
        attempts=2,
    )

    observer.on_task_finished({"task_id": "task_001"}, result)

    messages = _messages(manager)
    assert messages[0].content == "Task finished after 2 attempts"


def test_conversation_observer_uses_event_role_for_all_messages():
    manager = ConversationManager()
    observer = _observer(manager=manager)

    observer.on_task_started({"task_id": "task_001"}, attempt=1)
    observer.on_artifact_created({"task_id": "task_001"}, {"content": {}}, attempt=1)
    observer.on_quality_checked(
        {"task_id": "task_001"},
        QualityResult(passed=True, score=1.0),
        attempt=1,
    )
    observer.on_retry_decided(
        {"task_id": "task_001"},
        RetryDecision(
            should_retry=False,
            reason="quality passed",
            attempt=1,
            max_attempts=3,
        ),
        attempt=1,
    )

    messages = _messages(manager)
    assert [message.role for message in messages] == ["event", "event", "event", "event"]


def test_conversation_observer_uses_configured_employee_name():
    manager = ConversationManager()
    observer = _observer(manager=manager, employee_name="LoopObserver")

    observer.on_task_started({"task_id": "task_001"}, attempt=1)

    messages = _messages(manager)
    assert messages[0].employee_name == "LoopObserver"


def test_workflow_loop_with_conversation_observer_records_events():
    manager = ConversationManager()
    observer = _observer(manager=manager, conversation_id="workflow_loop")
    retry_decision = RetryDecision(
        should_retry=False,
        reason="quality passed",
        attempt=1,
        max_attempts=3,
    )
    loop = WorkflowLoop(
        task_executor=FakeTaskExecutor(),
        quality_checker=FakeQualityChecker([QualityResult(passed=True, score=0.95)]),
        retry_engine=FakeRetryEngine([retry_decision]),
        observer=observer,
    )

    result = loop.run({"task_id": "task_integration"})

    messages = _messages(manager, conversation_id="workflow_loop")
    assert result.attempts == 1
    assert [message.content for message in messages] == [
        "Task started: {'task_id': 'task_integration'}",
        "Artifact created on attempt 1",
        "Quality checked: passed=True, score=0.95",
        "Retry decided: should_retry=False, reason=quality passed",
        "Task finished after 1 attempts",
    ]
    assert [message.role for message in messages] == ["event"] * 5
    assert [message.employee_name for message in messages] == ["WorkflowLoop"] * 5
