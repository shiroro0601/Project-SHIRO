from dataclasses import dataclass
from typing import Any

from company.core.quality import QualityChecker, QualityResult
from company.core.retry import RetryDecision, RetryEngine
from company.core.task_executor import TaskExecutor


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
    ):
        self.task_executor = task_executor or TaskExecutor()
        self.quality_checker = quality_checker or QualityChecker()
        self.retry_engine = retry_engine or RetryEngine()

    def run(self, task) -> WorkflowLoopResult:
        attempts = 0

        while True:
            attempts += 1
            artifact = self.task_executor.execute(task)
            quality_result = self.quality_checker.check(artifact)
            retry_decision = self.retry_engine.decide(quality_result, attempt=attempts)

            if not retry_decision.should_retry:
                return WorkflowLoopResult(
                    artifact=artifact,
                    quality_result=quality_result,
                    retry_decision=retry_decision,
                    attempts=attempts,
                )
