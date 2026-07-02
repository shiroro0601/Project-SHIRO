from dataclasses import dataclass
from typing import Any

from company.core.quality import QualityChecker, QualityResult
from company.core.retry import RetryDecision, RetryEngine
from company.core.task_executor import TaskExecutor
from company.core.workflow_observer import NullWorkflowLoopObserver, WorkflowLoopObserver


@dataclass
class WorkflowLoopResult:
    artifact: Any
    quality_result: QualityResult
    retry_decision: RetryDecision
    attempts: int

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("attempts must be greater than or equal to 1.")


class WorkflowLoop:
    """
    1つのTaskに対して実行、品質チェック、再試行判断を制御する層。

    WorkflowV2全体の進行やBrain/Providerへの直接接続は担当しない。
    """

    def __init__(
        self,
        task_executor: TaskExecutor | None = None,
        quality_checker: QualityChecker | None = None,
        retry_engine: RetryEngine | None = None,
        observer: WorkflowLoopObserver | None = None,
    ):
        self.task_executor = task_executor or TaskExecutor()
        self.quality_checker = quality_checker or QualityChecker()
        self.retry_engine = retry_engine or RetryEngine()
        self.observer = observer or NullWorkflowLoopObserver()

    def run(self, task) -> WorkflowLoopResult:
        attempts = 0

        while True:
            attempts += 1
            self.observer.on_task_started(task, attempts)

            artifact = self.task_executor.execute(task)
            self.observer.on_artifact_created(task, artifact, attempts)

            quality_result = self.quality_checker.check(artifact)
            self.observer.on_quality_checked(task, quality_result, attempts)

            retry_decision = self.retry_engine.decide(quality_result, attempt=attempts)
            self.observer.on_retry_decided(task, retry_decision, attempts)

            if not retry_decision.should_retry:
                result = WorkflowLoopResult(
                    artifact=artifact,
                    quality_result=quality_result,
                    retry_decision=retry_decision,
                    attempts=attempts,
                )
                self.observer.on_task_finished(task, result)
                return result
