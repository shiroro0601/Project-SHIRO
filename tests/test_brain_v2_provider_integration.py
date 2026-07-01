import pytest

from company.brain.brain_v2 import BrainV2
from company.brain.provider import DummyProvider
from company.core.task import TaskType
from company.core.task_factory import TaskFactory


def test_brain_v2_uses_dummy_provider_by_default():
    task = TaskFactory.create_task(
        task_type=TaskType.PLANNING,
        instruction="企画を作成してください。",
    )

    result = BrainV2().ask(task)

    assert result["provider"] == "dummy"
    assert "DummyProvider response" in result["result"]


def test_brain_v2_accepts_dummy_provider():
    task = TaskFactory.create_task(
        task_type=TaskType.SCRIPT_WRITING,
        instruction="台本を作成してください。",
    )

    result = BrainV2(provider=DummyProvider()).ask(task)

    assert result["provider"] == "dummy"
    assert result["task_type"] == "script_writing"


def test_brain_v2_uses_custom_provider_result():
    class FakeProvider:
        def generate(self, task):
            return {
                "result": "fake provider response",
                "provider": "fake",
                "task_type": task.task_type.value,
            }

    task = TaskFactory.create_task(
        task_type=TaskType.DIRECTION,
        instruction="演出指示を作成してください。",
    )

    result = BrainV2(provider=FakeProvider()).ask(task)

    assert result == {
        "result": "fake provider response",
        "provider": "fake",
        "task_type": "direction",
    }


def test_brain_v2_propagates_provider_exception():
    class FailingProvider:
        def generate(self, task):
            raise RuntimeError("provider failed")

    task = TaskFactory.create_task(
        task_type=TaskType.QUALITY_CHECK,
        instruction="品質チェックをしてください。",
    )

    with pytest.raises(RuntimeError, match="provider failed"):
        BrainV2(provider=FailingProvider()).ask(task)
