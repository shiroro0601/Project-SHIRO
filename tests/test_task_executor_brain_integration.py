import pytest

from company.brain.brain_v2 import BrainV2
from company.core.task import TaskStatus, TaskType
from company.core.task_executor import TaskExecutor
from company.core.task_factory import TaskFactory


def test_task_executor_executes_with_brain_v2():
    task = TaskFactory.create_task(
        task_type=TaskType.SCRIPT_WRITING,
        instruction="台本を作成してください。",
        input_data={"plan": "猫の雑学企画"},
    )
    executor = TaskExecutor(brain=BrainV2())

    result = executor.execute(task)

    assert result is task
    assert task.status == TaskStatus.COMPLETED
    assert "DummyProvider response" in task.output_data["result"]
    assert task.output_data["provider"] == "dummy"
    assert task.output_data["task_type"] == "script_writing"
    assert task.output_data["instruction"] == "台本を作成してください。"
    assert task.output_data["input_data"] == {"plan": "猫の雑学企画"}


def test_task_executor_without_brain_keeps_dummy_behavior():
    task = TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="汎用タスクを実行してください。",
    )
    executor = TaskExecutor()

    executor.execute(task)

    assert task.status == TaskStatus.COMPLETED
    assert task.output_data["result"] == "Dummy execution completed for general."


def test_task_executor_marks_failed_when_brain_raises():
    class FailingBrain:
        def ask(self, task):
            raise RuntimeError("brain failed")

    task = TaskFactory.create_task(
        task_type=TaskType.QUALITY_CHECK,
        instruction="品質チェックをしてください。",
    )
    executor = TaskExecutor(brain=FailingBrain())

    with pytest.raises(RuntimeError, match="brain failed"):
        executor.execute(task)

    assert task.status == TaskStatus.FAILED
    assert task.started_at is not None
    assert task.finished_at is not None
    assert task.error == "brain failed"
