import pytest

from company.brain.provider import BaseProvider, DummyProvider
from company.core.task import TaskType
from company.core.task_factory import TaskFactory


def test_base_provider_generate_raises_not_implemented_error():
    task = TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="汎用タスクを実行してください。",
    )

    with pytest.raises(NotImplementedError):
        BaseProvider().generate(task)


def test_dummy_provider_generate_returns_dict():
    task = TaskFactory.create_task(
        task_type=TaskType.PLANNING,
        instruction="猫の意外な雑学について企画を作成してください。",
        input_data={"theme": "猫の意外な雑学"},
    )

    result = DummyProvider().generate(task)

    assert isinstance(result, dict)
    assert result["provider"] == "dummy"
    assert "DummyProvider response" in result["result"]
    assert result["task_type"] == "planning"
    assert result["instruction"] == "猫の意外な雑学について企画を作成してください。"
    assert result["input_data"] == {"theme": "猫の意外な雑学"}
