from company.brain.brain_v2 import BrainV2
from company.core.task import TaskType
from company.core.task_factory import TaskFactory


def test_brain_v2_ask_returns_dict():
    task = TaskFactory.create_task(
        task_type=TaskType.PLANNING,
        instruction="猫の意外な雑学について企画を作成してください。",
        input_data={"theme": "猫の意外な雑学"},
    )
    brain = BrainV2()

    result = brain.ask(task)

    assert isinstance(result, dict)
    assert "BrainV2 dummy response" in result["result"]
    assert result["task_type"] == "planning"
    assert result["instruction"] == "猫の意外な雑学について企画を作成してください。"
    assert result["input_data"] == {"theme": "猫の意外な雑学"}
