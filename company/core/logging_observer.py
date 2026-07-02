import logging
from typing import Any


class LoggingObserver:
    """
    WorkflowLoopのイベントを人間向けログとして記録するObserver。

    ConversationやCompanyMemoryには依存せず、ログ出力だけを担当する。
    """

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def on_task_started(self, task, attempt: int) -> None:
        self.logger.info("Task Started: attempt=%s task=%s", attempt, task)

    def on_artifact_created(self, task, artifact: Any, attempt: int) -> None:
        self.logger.info("Artifact Created: attempt=%s", attempt)

    def on_quality_checked(self, task, quality_result, attempt: int) -> None:
        message = (
            "Quality Passed"
            if quality_result.passed
            else "Quality Failed"
        )
        log = self.logger.info if quality_result.passed else self.logger.warning
        log(
            "%s: attempt=%s score=%s",
            message,
            attempt,
            quality_result.score,
        )

    def on_retry_decided(self, task, retry_decision, attempt: int) -> None:
        if retry_decision.should_retry:
            self.logger.warning(
                "Retry: attempt=%s reason=%s",
                attempt,
                retry_decision.reason,
            )
            return

        self.logger.info(
            "Retry Skipped: attempt=%s reason=%s",
            attempt,
            retry_decision.reason,
        )

    def on_task_finished(self, task, result) -> None:
        self.logger.info("Task Finished: attempts=%s", result.attempts)
