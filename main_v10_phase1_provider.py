from pprint import pprint

from company.brain.brain_v2 import BrainV2
from company.brain.provider import DummyProvider
from company.core.task import TaskType
from company.core.task_executor import TaskExecutor
from company.core.task_factory import TaskFactory


def main():
    print("================================")
    print("Project SHIRO Version1.0 Phase1-7")
    print("Provider Abstraction")
    print("================================")

    task = TaskFactory.create_task(
        task_type=TaskType.PLANNING,
        instruction="猫の意外な雑学について動画企画を作成してください。",
        input_data={
            "theme": "猫の意外な雑学",
            "platform": "YouTube Shorts",
        },
    )

    provider = DummyProvider()
    brain = BrainV2(provider=provider)
    executor = TaskExecutor(brain=brain)
    completed_task = executor.execute(task)

    print("")
    print("Completed Task")
    print("--------------------------------")
    pprint(completed_task.to_dict())

    print("")
    print("Provider")
    print("--------------------------------")
    print(completed_task.output_data["provider"])


if __name__ == "__main__":
    main()
