import logging

from company.core.logging_observer import LoggingObserver
from company.core.quality import QualityResult
from company.core.retry import RetryDecision
from company.core.workflow_loop import WorkflowLoopResult


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def messages(self):
        return [record.getMessage() for record in self.records]

    def levels(self):
        return [record.levelno for record in self.records]


def _logger():
    logger = logging.getLogger("project_shiro_test_logging_observer")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    handler = ListHandler()
    logger.addHandler(handler)
    return logger, handler


def test_logging_observer_logs_task_started():
    logger, handler = _logger()
    observer = LoggingObserver(logger=logger)

    observer.on_task_started({"task_id": "task_001"}, attempt=1)

    assert handler.messages() == ["Task Started: attempt=1 task={'task_id': 'task_001'}"]
    assert handler.levels() == [logging.INFO]


def test_logging_observer_logs_artifact_created():
    logger, handler = _logger()
    observer = LoggingObserver(logger=logger)

    observer.on_artifact_created(
        {"task_id": "task_001"},
        {"content": {"plan": "test"}},
        attempt=2,
    )

    assert handler.messages() == ["Artifact Created: attempt=2"]
    assert handler.levels() == [logging.INFO]


def test_logging_observer_logs_quality_passed():
    logger, handler = _logger()
    observer = LoggingObserver(logger=logger)

    observer.on_quality_checked(
        {"task_id": "task_001"},
        QualityResult(passed=True, score=0.95),
        attempt=1,
    )

    assert handler.messages() == ["Quality Passed: attempt=1 score=0.95"]
    assert handler.levels() == [logging.INFO]


def test_logging_observer_logs_quality_failed_as_warning():
    logger, handler = _logger()
    observer = LoggingObserver(logger=logger)

    observer.on_quality_checked(
        {"task_id": "task_001"},
        QualityResult(passed=False, score=0.4),
        attempt=1,
    )

    assert handler.messages() == ["Quality Failed: attempt=1 score=0.4"]
    assert handler.levels() == [logging.WARNING]


def test_logging_observer_logs_retry_as_warning():
    logger, handler = _logger()
    observer = LoggingObserver(logger=logger)

    observer.on_retry_decided(
        {"task_id": "task_001"},
        RetryDecision(
            should_retry=True,
            reason="quality failed",
            attempt=1,
            max_attempts=3,
        ),
        attempt=1,
    )

    assert handler.messages() == ["Retry: attempt=1 reason=quality failed"]
    assert handler.levels() == [logging.WARNING]


def test_logging_observer_logs_task_finished():
    logger, handler = _logger()
    observer = LoggingObserver(logger=logger)
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

    assert handler.messages() == ["Task Finished: attempts=2"]
    assert handler.levels() == [logging.INFO]


def test_logging_observer_uses_default_logger_when_not_specified():
    observer = LoggingObserver()

    assert observer.logger.name == "company.core.logging_observer"
