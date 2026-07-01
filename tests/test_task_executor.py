import pytest

from company.core.task import TaskStatus, TaskType
from company.core.task_executor import TaskExecutor
from company.core.task_factory import TaskFactory


def test_task_executor_completes_task():
    task = TaskFactory.create_task(
        task_type=TaskType.PLANNING,
        instruction="猫の意外な雑学について企画を作成してください。",
        input_data={
            "theme": "猫の意外な雑学",
        },
    )
    executor = TaskExecutor()

    result = executor.execute(task)

    assert result is task
    assert task.status == TaskStatus.COMPLETED
    assert task.started_at is not None
    assert task.finished_at is not None
    assert task.error is None
    assert task.output_data["task_id"] == task.task_id
    assert task.output_data["task_type"] == "planning"
    assert task.output_data["instruction"] == "猫の意外な雑学について企画を作成してください。"
    assert task.output_data["input_data"]["theme"] == "猫の意外な雑学"
    assert "Dummy execution completed" in task.output_data["result"]


def test_task_executor_completes_task_without_input_data():
    task = TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="汎用タスクを実行してください。",
    )
    executor = TaskExecutor()

    result = executor.execute(task)

    assert result.status == TaskStatus.COMPLETED
    assert result.output_data["input_data"] == {}
    assert result.output_data["result"] == "Dummy execution completed for general."


def test_task_executor_marks_task_failed_and_raises_on_error():
    class FailingTaskExecutor(TaskExecutor):
        def _execute_dummy_brain(self, task):
            raise RuntimeError("dummy executor error")

    task = TaskFactory.create_task(
        task_type=TaskType.QUALITY_CHECK,
        instruction="品質チェックをしてください。",
    )
    executor = FailingTaskExecutor()

    with pytest.raises(RuntimeError, match="dummy executor error"):
        executor.execute(task)

    assert task.status == TaskStatus.FAILED
    assert task.started_at is not None
    assert task.finished_at is not None
    assert task.error == "dummy executor error"
