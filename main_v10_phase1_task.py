from company.core.task import TaskType
from company.core.task_factory import TaskFactory


def main():
    print("================================")
    print("Project SHIRO Version1.0 Phase1-2")
    print("Task層 テスト起動")
    print("================================")

    task = TaskFactory.create_task(
        task_type=TaskType.PLANNING,
        instruction="猫の意外な雑学について動画企画を作成してください。",
        input_data={
            "theme": "猫の意外な雑学",
            "platform": "YouTube Shorts",
        },
    )

    print("")
    print("Task作成完了")
    print("--------------------------------")
    print(task.to_dict())

    task.start()

    print("")
    print("Task開始")
    print("--------------------------------")
    print(task.to_dict())

    task.complete(
        {
            "plan": "猫の知られざる習性を3つ紹介するショート動画",
        }
    )

    print("")
    print("Task完了")
    print("--------------------------------")
    print(task.to_dict())


if __name__ == "__main__":
    main()