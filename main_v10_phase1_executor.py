from company.core.task import TaskType
from company.core.task_executor import TaskExecutor
from company.core.task_factory import TaskFactory


def main():
    print("================================")
    print("Project SHIRO Version1.0 Phase1-3")
    print("TaskExecutor テスト起動")
    print("================================")

    task = TaskFactory.create_task(
        task_type=TaskType.PLANNING,
        instruction="猫の意外な雑学について動画企画を作成してください。",
        input_data={
            "theme": "猫の意外な雑学",
            "platform": "YouTube Shorts",
        },
    )

    executor = TaskExecutor()
    executed_task = executor.execute(task)

    print("")
    print("TaskExecutor 実行完了")
    print("--------------------------------")
    print(executed_task.to_dict())


if __name__ == "__main__":
    main()
