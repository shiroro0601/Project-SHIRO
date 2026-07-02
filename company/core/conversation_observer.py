from typing import Any

from company.core.conversation import ConversationManager


class ConversationObserver:
    """
    WorkflowLoopのイベントをConversation Memoryへ記録するObserver。

    WorkflowLoop本体はConversationに依存せず、このObserverを通じて短期記憶へ接続する。
    """

    def __init__(
        self,
        conversation_manager: ConversationManager,
        conversation_id: str,
        employee_name: str = "system",
    ):
        self.conversation_manager = conversation_manager
        self.conversation_id = conversation_id
        self.employee_name = employee_name

    def on_task_started(self, task, attempt: int) -> None:
        self._add_message(f"Task started: {task}")

    def on_artifact_created(self, task, artifact: Any, attempt: int) -> None:
        self._add_message(f"Artifact created on attempt {attempt}")

    def on_quality_checked(self, task, quality_result, attempt: int) -> None:
        self._add_message(
            f"Quality checked: passed={quality_result.passed}, score={quality_result.score}"
        )

    def on_retry_decided(self, task, retry_decision, attempt: int) -> None:
        self._add_message(
            "Retry decided: "
            f"should_retry={retry_decision.should_retry}, reason={retry_decision.reason}"
        )

    def on_task_finished(self, task, result) -> None:
        self._add_message(f"Task finished after {result.attempts} attempts")

    def _add_message(self, content: str) -> None:
        self.conversation_manager.add_message(
            workflow_id=self.conversation_id,
            employee_name=self.employee_name,
            role="event",
            content=content,
        )
