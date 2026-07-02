from typing import Any, List, Protocol


class WorkflowLoopObserver(Protocol):
    def on_task_started(self, task, attempt: int) -> None:
        ...

    def on_artifact_created(self, task, artifact: Any, attempt: int) -> None:
        ...

    def on_quality_checked(self, task, quality_result, attempt: int) -> None:
        ...

    def on_retry_decided(self, task, retry_decision, attempt: int) -> None:
        ...

    def on_task_finished(self, task, result) -> None:
        ...


class NullWorkflowLoopObserver:
    def on_task_started(self, task, attempt: int) -> None:
        pass

    def on_artifact_created(self, task, artifact: Any, attempt: int) -> None:
        pass

    def on_quality_checked(self, task, quality_result, attempt: int) -> None:
        pass

    def on_retry_decided(self, task, retry_decision, attempt: int) -> None:
        pass

    def on_task_finished(self, task, result) -> None:
        pass


class CompositeWorkflowLoopObserver:
    """
    複数Observerへイベントを順番に通知する。

    個別Observerの例外はerrorsへ保存し、他Observerへの通知は継続する。
    """

    def __init__(self, observers: List[WorkflowLoopObserver] | None = None):
        self.observers = observers or []
        self.errors: List[Exception] = []

    def on_task_started(self, task, attempt: int) -> None:
        self._notify("on_task_started", task, attempt)

    def on_artifact_created(self, task, artifact: Any, attempt: int) -> None:
        self._notify("on_artifact_created", task, artifact, attempt)

    def on_quality_checked(self, task, quality_result, attempt: int) -> None:
        self._notify("on_quality_checked", task, quality_result, attempt)

    def on_retry_decided(self, task, retry_decision, attempt: int) -> None:
        self._notify("on_retry_decided", task, retry_decision, attempt)

    def on_task_finished(self, task, result) -> None:
        self._notify("on_task_finished", task, result)

    def _notify(self, method_name: str, *args) -> None:
        for observer in self.observers:
            try:
                getattr(observer, method_name)(*args)
            except Exception as e:
                self.errors.append(e)
